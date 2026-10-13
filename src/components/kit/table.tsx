import type { ReactNode } from "react";
import "./kit.css";

export interface Column<Row> {
  key: string;
  header: string;
  cell: (row: Row) => ReactNode;
}

/**
 * A table from the starter kit. Wide enough, it is a table; narrow (a phone, or a narrow column), each row becomes
 * a block of label and value lines, so it never scrolls sideways. Long words wrap inside their cell.
 */
export function Table<Row>({
  columns,
  rows,
  rowKey,
  caption,
}: {
  columns: Column<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
  caption?: string;
}) {
  return (
    <div className="kit-table-wrap">
      <table className="kit-table">
        {caption ? <caption className="kit-table-caption">{caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((c) => (
                <td key={c.key} data-label={c.header}>
                  {c.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
