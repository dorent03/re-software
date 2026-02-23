/**
 * Validate that a value is not empty.
 * @param {*} value
 * @param {string} fieldName
 * @returns {string|null} error message or null
 */
export function required(value, fieldName = 'Feld') {
  if (value === null || value === undefined || String(value).trim() === '') {
    return `${fieldName} ist erforderlich`
  }
  return null
}

/**
 * Validate email format.
 * @param {string} value
 * @returns {string|null}
 */
export function email(value) {
  if (!value) return null
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(value) ? null : 'Ungültige E-Mail-Adresse'
}

/**
 * Validate minimum string length.
 * @param {string} value
 * @param {number} min
 * @param {string} fieldName
 * @returns {string|null}
 */
export function minLength(value, min, fieldName = 'Feld') {
  if (!value || value.length < min) {
    return `${fieldName} muss mindestens ${min} Zeichen lang sein`
  }
  return null
}

/**
 * Validate that a number is greater than zero.
 * @param {number} value
 * @param {string} fieldName
 * @returns {string|null}
 */
export function positiveNumber(value, fieldName = 'Wert') {
  if (value === null || value === undefined || Number(value) <= 0) {
    return `${fieldName} muss größer als 0 sein`
  }
  return null
}

/**
 * Validate a number range (inclusive).
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @param {string} fieldName
 * @returns {string|null}
 */
export function numberRange(value, min, max, fieldName = 'Wert') {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue) || numericValue < min || numericValue > max) {
    return `${fieldName} muss zwischen ${min} und ${max} liegen`
  }
  return null
}

/**
 * Validate VAT rate against supported rates.
 * @param {number} value
 * @returns {string|null}
 */
export function vatRate(value) {
  const allowed = [0, 0.07, 0.19]
  const numericValue = Number(value)
  return allowed.includes(numericValue) ? null : 'Ungültiger MwSt.-Satz'
}

/**
 * Validate payment terms between 0 and 365 days.
 * @param {number} value
 * @returns {string|null}
 */
export function paymentTerms(value) {
  return numberRange(value, 0, 365, 'Zahlungsziel')
}

/**
 * Validate discount percent (0-100).
 * @param {number} value
 * @returns {string|null}
 */
export function discountPercent(value) {
  return numberRange(value, 0, 100, 'Rabatt')
}

/**
 * Run multiple validators on a value and return the first error.
 * @param {*} value
 * @param {Function[]} validators
 * @returns {string|null}
 */
export function validate(value, ...validators) {
  for (const fn of validators) {
    const err = fn(value)
    if (err) return err
  }
  return null
}
