/**
 * Formats a UTC date string (e.g. from backend) to local date and time.
 * @param dateStr ISO date string from backend
 * @returns Formatted string in local timezone
 */
export function formatLocalDate(dateStr: string | undefined): string {
  if (!dateStr) return "-";
  
  // Ensure we treat it as UTC. If no 'Z' or offset, append 'Z'.
  const utcStr = (dateStr.includes('Z') || dateStr.includes('+')) 
    ? dateStr 
    : dateStr + 'Z';
    
  const d = new Date(utcStr);
  if (isNaN(d.getTime())) return dateStr;

  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}`;
}
