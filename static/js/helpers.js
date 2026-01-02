/**
 * Helper para extraer la alteración de una nota en formato string
 * @param {string} noteStr - Nota en formato "C#4", "Db3", "E4", etc
 * @returns {string|null} - '#', 'b', 'n', o null si es natural sin marca explícita
 */
function getAccidentalFromNote(noteStr) {
    if (!noteStr) return null;

    if (noteStr.includes('#')) return '#';
    if (noteStr.includes('b')) return 'b';
    if (noteStr.includes('n')) return 'n';

    // Si no tiene marca explícita, es natural
    return null;
}

/**
 * Extrae el nombre base de la nota (sin alteración ni octava)
 * @param {string} noteStr - Nota en formato "C#4", "Db3", "E4", etc
 * @returns {string} - 'C', 'D', 'E', 'F', 'G', 'A', 'B'
 */
function getNoteBaseName(noteStr) {
    if (!noteStr) return '';

    // Tomar primer carácter (la letra de la nota)
    return noteStr[0].toUpperCase();
}

// Exportar helpers globalmente para uso en AudioStudio
window.getAccidentalFromNote = getAccidentalFromNote;
window.getNoteBaseName = getNoteBaseName;
