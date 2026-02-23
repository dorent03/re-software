import { db } from '@/db'

const TABLES = ['company', 'customers', 'products', 'documents', 'counters']

export async function exportAllData() {
  const snapshot = {}
  for (const tableName of TABLES) {
    snapshot[tableName] = await db.table(tableName).toArray()
  }
  snapshot.exported_at = new Date().toISOString()

  const payload = JSON.stringify(snapshot, null, 2)
  const blob = new Blob([payload], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `re-software-backup-${new Date().toISOString().slice(0, 10)}.json`
  anchor.click()
  URL.revokeObjectURL(url)
}

function parseImportPayload(rawText) {
  const parsed = JSON.parse(rawText)
  for (const tableName of TABLES) {
    if (!Array.isArray(parsed[tableName])) {
      throw new Error(`Import-Datei enthält keine gültige Tabelle: ${tableName}`)
    }
  }
  return parsed
}

export async function importAllData(file) {
  const text = await file.text()
  const payload = parseImportPayload(text)

  await db.transaction('rw', db.company, db.customers, db.products, db.documents, db.counters, async () => {
    for (const tableName of TABLES) {
      const table = db.table(tableName)
      await table.clear()
      if (payload[tableName].length > 0) {
        await table.bulkAdd(payload[tableName])
      }
    }
  })
}
