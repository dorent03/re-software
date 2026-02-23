import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import { formatCurrency } from '@/utils/helpers'

function formatDate(dateValue) {
  if (!dateValue) return '-'
  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return String(dateValue)
  return parsed.toLocaleDateString('de-DE')
}

export async function buildDocumentPdf(document, company, customer) {
  const pdf = new jsPDF({ unit: 'mm', format: 'a4' })
  const marginLeft = 14

  pdf.setFontSize(18)
  pdf.text(company?.name || 'RE-Software', marginLeft, 16)
  pdf.setFontSize(10)
  pdf.text(`${company?.street || ''}, ${company?.zip || ''} ${company?.city || ''}`.trim(), marginLeft, 22)
  pdf.text(`${company?.country || ''}`, marginLeft, 27)

  pdf.setFontSize(14)
  pdf.text('Rechnung', 150, 16)
  pdf.setFontSize(10)
  pdf.text(`Nr: ${document.document_number || '-'}`, 150, 22)
  pdf.text(`Datum: ${formatDate(document.issue_date || document.created_at)}`, 150, 27)
  pdf.text(`Faellig: ${formatDate(document.due_date)}`, 150, 32)

  pdf.setFontSize(11)
  pdf.text('Kunde', marginLeft, 42)
  pdf.setFontSize(10)
  pdf.text(customer?.name || document.customer_name || '-', marginLeft, 48)
  pdf.text(customer?.street || '-', marginLeft, 53)
  pdf.text(`${customer?.zip_code || ''} ${customer?.city || ''}`.trim(), marginLeft, 58)

  const rows = (document.items || []).map((item, index) => [
    String(index + 1),
    item.name || item.description || '-',
    String(item.quantity || 0),
    item.unit || '-',
    formatCurrency(item.unit_price || 0),
    `${((item.vat_rate || 0) * 100).toFixed(0)}%`,
    formatCurrency(item.gross_amount || 0),
  ])

  autoTable(pdf, {
    startY: 66,
    head: [['Pos', 'Bezeichnung', 'Menge', 'Einheit', 'Preis', 'MwSt', 'Brutto']],
    body: rows,
    styles: { fontSize: 9 },
    headStyles: { fillColor: [37, 99, 235] },
  })

  const endY = pdf.lastAutoTable?.finalY || 120
  pdf.setFontSize(10)
  pdf.text(`Netto: ${formatCurrency(document.totals?.net || 0)}`, 140, endY + 10)
  pdf.text(`MwSt: ${formatCurrency(document.totals?.vat || 0)}`, 140, endY + 16)
  pdf.setFontSize(12)
  pdf.text(`Gesamt: ${formatCurrency(document.totals?.gross || 0)}`, 140, endY + 24)

  if (document.notes) {
    pdf.setFontSize(9)
    pdf.text(`Hinweis: ${document.notes}`, marginLeft, endY + 34, { maxWidth: 180 })
  }

  return pdf
}

export async function buildDocumentPdfBlob(document, company, customer) {
  const pdf = await buildDocumentPdf(document, company, customer)
  return pdf.output('blob')
}
