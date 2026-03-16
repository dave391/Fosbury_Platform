CONTESTO
In core/database.py riga 13, l'engine è creato così:
pythonengine = create_async_engine(database_url, echo=False)
Nessuna configurazione del connection pool. Il sistema usa i default di SQLAlchemy.
Con Supabase, le connessioni inattive vengono chiuse dal server dopo un timeout.
Se succede, la prossima richiesta utente riceve un errore.
OBIETTIVO
Aggiungere configurazione minima del pool per robustezza.
COSA FARE
Sostituire la riga 13 di core/database.py:
pythonengine = create_async_engine(database_url, echo=False)
Con:
pythonengine = create_async_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
)
Cosa fa ogni parametro:

pool_pre_ping=True: prima di usare una connessione, verifica che sia ancora viva.
Se è morta, ne crea una nuova. Previene errori da connessioni stale.
pool_size=5: mantiene 5 connessioni aperte (sufficiente per pochi utenti)
max_overflow=5: permette fino a 5 connessioni extra in caso di picco
pool_recycle=300: ricrea le connessioni ogni 5 minuti, evitando che Supabase
le chiuda per inattività

Non servono altre modifiche.
VINCOLI

Modificare solo questa riga, nient'altro nel file
Non aggiungere dipendenze

TEST DI VERIFICA

L'app si avvia senza errori
Le pagine funzionano normalmente