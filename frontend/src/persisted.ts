import { useEffect, useState } from 'react'
export function useSessionValue(key:string) {
  const [value,setValue]=useState(()=>{try{return sessionStorage.getItem(key)||''}catch{return ''}})
  useEffect(()=>{try{sessionStorage.setItem(key,value)}catch{/* Session persistence may be disabled by the browser. */}},[key,value])
  return [value,setValue] as const
}
