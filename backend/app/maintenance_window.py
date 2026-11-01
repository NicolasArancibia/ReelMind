"""User-launched Windows companion; no web endpoint can invoke shell commands."""
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
from datetime import datetime,timezone
from uuid import uuid4
import tkinter as tk
from tkinter import ttk,filedialog,messagebox

PROJECT=Path(__file__).resolve().parents[2]
RUNTIME=PROJECT/'.local/runtime.json'

def read_runtime():return json.loads(RUNTIME.read_text(encoding='utf-8-sig'))

def validate_recovery(path):
    from app.maintenance import external
    path=external(Path(path));report=json.loads(path.read_text(encoding='utf-8-sig'))
    if report.get('verified') is not True or not re.fullmatch(r'reelmind_restore_[0-9a-f]{32}',report.get('database','')):
        raise ValueError('No es una verificación de restauración reconocida.')
    root=external(Path(report['data_root']))
    if root!=(path.parent/'data').resolve() or not root.is_dir():raise ValueError('El almacén no corresponde a esta verificación.')
    return report


def store_configuration(values,runtime_path=RUNTIME):
    """Preserve the complete old config; only change store/database, never credentials."""
    current=json.loads(runtime_path.read_text(encoding='utf-8-sig'))
    name=values.get('DatabaseName','reelmind')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',name):raise ValueError('Nombre de base no válido.')
    if values.get('DataRoot'):
        from app.maintenance import external
        external(Path(values['DataRoot']))
    folder=Path(current['CredentialPath']).parent.parent/'configuration-history';folder.mkdir(parents=True,exist_ok=True)
    backup=folder/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex+'.json')
    backup.write_text(json.dumps(current,indent=2),encoding='utf-8')
    for key in ('DataRoot','DatabaseName'):
        if key in values:current[key]=values[key]
        else:current.pop(key,None)
    temporary=runtime_path.with_suffix('.next.json');temporary.write_text(json.dumps(current,indent=2),encoding='utf-8');os.replace(temporary,runtime_path)
    return backup


class MaintenanceWindow:
    def __init__(self,root):
        self.root=root;self.busy=False;self.events=queue.Queue();self.buttons=[];self.report_path=None;self.temporaries=[]
        root.title('ReelMind · Mantenimiento local');root.geometry('800x680');root.configure(bg='#101a13')
        style=ttk.Style();style.theme_use('clam');style.configure('TFrame',background='#101a13');style.configure('TLabel',background='#101a13',foreground='#d7e8dc',font=('Segoe UI',11));style.configure('TButton',padding=9,font=('Segoe UI',10))
        frame=ttk.Frame(root,padding=22);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Tu biblioteca, bajo tu control',font=('Segoe UI',19)).pack(anchor='w')
        ttk.Label(frame,text='El mantenimiento detiene los servicios y conserva los datos originales.',wraplength=730).pack(anchor='w',pady=(8,16))
        actions=ttk.Frame(frame);actions.pack(fill='x')
        for index,(label,command) in enumerate([('Abrir app',lambda:self.run(lambda:self.script('start.ps1',['-OpenBrowser']))),('Detener app',lambda:self.run(self.stop)),('Crear copia…',self.backup),('Verificar restauración…',self.restore),('Elegir copia verificada…',self.choose_report),('Preparar modelos…',self.prepare),('Revisar temporales',self.list_temporary)]):
            button=ttk.Button(actions,text=label,command=command);self.buttons.append(button);button.grid(row=index//3,column=index%3,sticky='ew',padx=3,pady=4)
        for column in range(3):actions.columnconfigure(column,weight=1)
        recovery=ttk.Frame(frame);recovery.pack(fill='x',pady=10)
        self.button(recovery,'Migrar copia verificada',self.migrate_copy);self.button(recovery,'Usar copia verificada',self.activate);self.button(recovery,'Volver a configuración anterior…',self.revert)
        ttk.Label(frame,text='Verifica y revisa la copia antes de activarla. Los modelos se preparan aparte.',wraplength=730).pack(anchor='w')
        self.output=tk.Text(frame,height=12,bg='#08110b',fg='#c4d4c9',insertbackground='#c4d4c9',wrap='word',font=('Consolas',10));self.output.pack(fill='both',expand=True,pady=10)
        self.status=tk.StringVar(value='Listo. No hay mantenimiento en curso.');ttk.Label(frame,textvariable=self.status,wraplength=730).pack(anchor='w')
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.drain)
    def button(self,frame,label,command):
        button=ttk.Button(frame,text=label,command=command);button.pack(side='left',padx=(0,6),pady=4);self.buttons.append(button);return button
    def log(self,value):self.events.put(('log',str(value)))
    def drain(self):
        try:
            while True:
                event,value=self.events.get_nowait()
                if event=='log':self.output.insert('end',value+'\n');self.output.see('end')
                elif event=='done':
                    self.busy=False;self.status.set(value)
                    for button in self.buttons:button.configure(state='normal')
                elif event=='temporary':self.show_temporaries(value)
        except queue.Empty:pass
        self.root.after(100,self.drain)
    def run(self,operation):
        if self.busy:return
        self.busy=True;self.status.set('En curso. No cierres esta ventana; el original se conserva.')
        for button in self.buttons:button.configure(state='disabled')
        def worker():
            try:operation();self.events.put(('done','Operación terminada. Revisa el resultado.'))
            except Exception as exc:self.log(f'{type(exc).__name__}: {exc}');self.events.put(('done','Operación incompleta. Se conservan los intentos y los originales.'))
        threading.Thread(target=worker,daemon=True).start()
    def script(self,name,args=None,overrides=None):
        env={k:v for k,v in os.environ.items() if k not in {'PGPASSWORD','PGUSER','PGDATABASE','REELMIND_DATA_ROOT','REELMIND_ADMIN_PASSWORD','REELMIND_ADMIN_USER'}}
        env.update(PYTHONUTF8='1');env.update(overrides or {})
        process=subprocess.Popen(['powershell.exe','-NoProfile','-File',str(PROJECT/'scripts'/name),*(args or [])],cwd=PROJECT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        results=[]
        for line in process.stdout:
            self.log(line.rstrip())
            try:
                value=json.loads(line)
                if isinstance(value,dict):results.append(value)
            except ValueError:pass
        if process.wait():raise RuntimeError('El comando no terminó correctamente. Revisa el resultado anterior.')
        return results[-1] if results else {}
    def stop(self):
        import httpx,time
        with httpx.Client(base_url='http://127.0.0.1:8000',trust_env=False,timeout=5) as client:
            try:
                client.post('/api/processing/stop').raise_for_status()
                current=client.get('/api/retrieval/status').json().get('current')
                if current:client.post('/api/retrieval/tasks/'+current['id']+'/stop').raise_for_status()
                for _ in range(120):
                    processing=client.get('/api/processing').json()
                    task=client.get('/api/retrieval/status').json().get('current')
                    if processing['state']=='stopped' and task is None:break
                    time.sleep(.5)
                else:raise RuntimeError('La tarea no se detuvo a tiempo. No se inició mantenimiento.')
            except httpx.ConnectError:pass
        self.script('stop.ps1')
    def maintenance(self,operation):
        self.stop()
        try:return operation()
        finally:self.script('start.ps1')
    def backup(self):
        folder=filedialog.askdirectory(title='Destino privado de la copia (mejor en otro disco)')
        if folder:self.run(lambda:self.maintenance(lambda:self.script('library-backup.ps1',['-Action','Backup','-Destination',folder])))
    def restore(self):
        folder=filedialog.askdirectory(title='Carpeta de una copia propia con manifest.json y database.dump')
        if not folder:return
        def operation():
            result=self.maintenance(lambda:self.script('library-backup.ps1',['-Action','RestoreVerify','-Bundle',folder]))
            self.report_path=Path(result['data_root']).parent/'verification.json';self.log('Copia verificada. El almacén principal no se cambió.')
        self.run(operation)
    def choose_report(self):
        name=filedialog.askopenfilename(title='Selecciona verification.json o activation-readiness.json',filetypes=[('Verificación JSON','*.json')])
        if not name:return
        try:self.log(json.dumps(validate_recovery(name),ensure_ascii=False));self.report_path=Path(name)
        except Exception as exc:messagebox.showerror('Copia no válida',str(exc))
    def migrate_copy(self):
        if not self.report_path:messagebox.showinfo('Elige una copia','Primero verifica o selecciona una copia restaurada.');return
        if not messagebox.askyesno('Migrar copia aislada','Se respaldará y actualizará únicamente la copia restaurada. ¿Continuar?'):return
        path=self.report_path
        def operation():
            report=validate_recovery(path);env={'PGDATABASE':report['database'],'REELMIND_DATA_ROOT':report['data_root']}
            def migrate():
                self.script('backend.ps1',['-Action','Migrate'],env);self.script('backend.ps1',['-Action','RecoveryCheck'],env)
            self.maintenance(migrate)
            from app.main import REVISION
            report.update(schema=REVISION,original_restore_report=str(path),migrated=True)
            ready=path.parent/'activation-readiness.json';ready.write_text(json.dumps(report,indent=2),encoding='utf-8');self.report_path=ready
            self.log('Copia migrada y comprobada por API. Puedes revisarla antes de activarla.')
        self.run(operation)
    def activate(self):
        if not self.report_path:messagebox.showinfo('Elige una copia','Primero verifica o selecciona una copia restaurada.');return
        try:
            report=validate_recovery(self.report_path)
            from app.main import REVISION
            if report['schema']!=REVISION:raise ValueError('La copia necesita Migrar copia verificada antes de usarla con esta versión.')
        except Exception as exc:messagebox.showerror('No se activó',str(exc));return
        if not messagebox.askyesno('Cambiar almacén activo',f"Se usará {report['database']}\n{report['data_root']}\nEl original y la configuración previa se conservarán. ¿Activar esta copia?"):return
        def operation():
            self.stop()
            try:self.script('backend.ps1',['-Action','RecoveryCheck'],{'PGDATABASE':report['database'],'REELMIND_DATA_ROOT':report['data_root']})
            except Exception:
                self.script('start.ps1');raise
            previous=store_configuration({'DatabaseName':report['database'],'DataRoot':report['data_root']});self.log('Configuración previa: '+str(previous));self.script('start.ps1',['-OpenBrowser'])
        self.run(operation)
    def revert(self):
        runtime=read_runtime();folder=Path(runtime['CredentialPath']).parent.parent/'configuration-history'
        name=filedialog.askopenfilename(title='Configuración previa a recuperar',initialdir=str(folder),filetypes=[('Configuración JSON','*.json')])
        if not name:return
        path=Path(name).resolve()
        if not path.is_relative_to(folder.resolve()):messagebox.showerror('Destino no válido','Selecciona una configuración de configuration-history.');return
        if not messagebox.askyesno('Volver al almacén anterior','Se conservará también la configuración actual. ¿Continuar?'):return
        def operation():
            previous=json.loads(path.read_text(encoding='utf-8-sig'));self.stop();store_configuration({k:previous[k] for k in ('DataRoot','DatabaseName') if k in previous});self.script('start.ps1',['-OpenBrowser'])
        self.run(operation)
    def prepare(self):
        if not messagebox.askyesno('Preparación explícita','Se detendrá la app y se prepararán sus modelos configurados. Si faltan pesos se descargarán; puede requerir varios GB. ¿Continuar?'):return
        self.run(lambda:self.maintenance(lambda:[self.script('backend.ps1',['-Action',action]) for action in ('PrepareAudio','PrepareAV','PrepareSearch')]))
    def list_temporary(self):
        def operation():
            result=self.maintenance(lambda:self.script('library-backup.ps1',['-Action','ListTemporary']));self.events.put(('temporary',result.get('temporaries',[])))
        self.run(operation)
    def show_temporaries(self,rows):
        window=tk.Toplevel(self.root);window.title('Temporales revisables · No incluye originales');window.geometry('750x430')
        listing=tk.Listbox(window,selectmode='extended',font=('Consolas',10));listing.pack(fill='both',expand=True)
        for row in rows:listing.insert('end',f"{row['relative']} · {row['size_bytes']} bytes")
        def remove():
            selected=[rows[i] for i in listing.curselection()]
            if not selected:return
            if not messagebox.askyesno('Eliminar temporales seleccionados',f'Se eliminarán definitivamente {len(selected)} temporales revisados. No se tocarán vídeos, modelos o copias. ¿Continuar?'):return
            window.destroy()
            def operation():
                runtime=read_runtime();folder=Path(runtime['CredentialPath']).parent.parent/'maintenance';folder.mkdir(exist_ok=True)
                selection=folder/(uuid4().hex+'.json');selection.write_text(json.dumps(selected),encoding='utf-8')
                self.maintenance(lambda:self.script('library-backup.ps1',['-Action','CleanTemporary','-Selection',str(selection)]))
            self.run(operation)
        ttk.Button(window,text='Eliminar selección revisada',command=remove).pack(pady=8)
        ttk.Label(window,text='Hasta 1000 archivos por revisión. Si cambiaron, se rechazará su eliminación.').pack()
    def close(self):
        if self.busy:messagebox.showinfo('Operación en curso','Espera a que termine. Esta ventana conserva el resultado de mantenimiento.');return
        self.root.destroy()

def main():
    root=tk.Tk();MaintenanceWindow(root);root.mainloop()

if __name__=='__main__':main()
