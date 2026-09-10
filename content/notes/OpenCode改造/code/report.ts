// Synthetic teaching contract: unquoted CSV, one currency, non-negative amounts.
export type Report = {
  rowCount: number;
  departments: { name: string; cents: string }[];
  totalCents: string;
};

export function amountToCents(value: string): bigint {
  if (!/^(0|[1-9]\d*)\.\d{2}$/.test(value)) throw new Error(`INVALID_AMOUNT: ${value}`);
  const [whole, fraction] = value.split('.');
  return BigInt(whole) * 100n + BigInt(fraction);
}

export function summarize(csv: string): Report {
  const lines = csv.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n');
  if (lines[0] !== 'record_id,department,amount') throw new Error('INVALID_HEADER');
  if (lines.length < 2) throw new Error('EMPTY_INPUT');
  const seen = new Set<string>();
  const totals = new Map<string, bigint>();
  for (const [index, line] of lines.slice(1).entries()) {
    const columns = line.split(',');
    if (columns.length !== 3 || line.includes('"')) throw new Error(`INVALID_CSV: line ${index + 2}`);
    const [id, department, amount] = columns;
    if (!/^[A-Za-z0-9_-]+$/.test(id)) throw new Error(`INVALID_ID: line ${index + 2}`);
    // Restrict labels so this tiny CSV writer cannot create a spreadsheet formula.
    if (!/^[\p{L}\p{N}_][\p{L}\p{N}_ -]{0,39}$/u.test(department)) {
      throw new Error(`INVALID_DEPARTMENT: line ${index + 2}`);
    }
    if (seen.has(id)) throw new Error(`DUPLICATE_ID: ${id}`);
    seen.add(id);
    totals.set(department, (totals.get(department) ?? 0n) + amountToCents(amount));
  }
  const departments = [...totals].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
    .map(([name, cents]) => ({ name, cents: cents.toString() }));
  return {
    rowCount: seen.size,
    departments,
    totalCents: [...totals.values()].reduce((sum, value) => sum + value, 0n).toString(),
  };
}

export function formatCents(cents: string): string {
  const value = BigInt(cents);
  return `${value / 100n}.${(value % 100n).toString().padStart(2, '0')}`;
}

export function reportCsv(report: Report): string {
  return 'department,amount\n' + report.departments
    .map(row => `${row.name},${formatCents(row.cents)}`).join('\n') + '\n';
}
