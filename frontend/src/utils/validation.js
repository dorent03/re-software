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
