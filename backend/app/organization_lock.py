from sqlalchemy import text
def lock_organization(session):
    # Serialize taxonomy changes before taking source locks; unrelated reads remain concurrent.
    session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':0x5245454C4F5247})
