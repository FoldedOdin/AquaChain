/**
 * Date Formatting Utilities
 * Consistent DD-MM-YYYY format across the application
 */

/**
 * Format date to DD-MM-YYYY
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  return `${day}-${month}-${year}`;
}

/**
 * Format date to DD-MM-YYYY HH:MM
 */
export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${day}-${month}-${year} ${hours}:${minutes}`;
}

/**
 * Format date to long format (e.g., "6 November 2025")
 */
export function formatDateLong(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });
}

/**
 * Format relative time (e.g., "2h ago", "Just now")
 */
export function formatRelativeTime(date: Date | string): string {
  // Handle string dates - ensure proper parsing of ISO timestamps with microseconds
  let d: Date;
  if (typeof date === 'string') {
    // Python datetime.isoformat() includes microseconds, which JS Date handles correctly
    // But we need to ensure it's treated as UTC
    d = new Date(date);
    
    // Debug: Log the parsing
    console.log(`🕐 Parsing timestamp: ${date}`);
    console.log(`🕐 Parsed as Date: ${d.toISOString()}`);
    console.log(`🕐 Local time: ${d.toLocaleString()}`);
  } else {
    d = date;
  }
  
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  console.log(`🕐 Time difference: ${minutes} minutes (${hours} hours)`);

  if (minutes < 1) {
    return 'Just now';
  } else if (minutes < 60) {
    return `${minutes}m ago`;
  } else if (hours < 24) {
    return `${hours}h ago`;
  } else if (days === 1) {
    return 'Yesterday';
  } else if (days < 7) {
    return `${days}d ago`;
  } else {
    return formatDate(d);
  }
}
