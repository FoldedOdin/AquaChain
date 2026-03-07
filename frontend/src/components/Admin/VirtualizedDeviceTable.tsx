/**
 * Virtualized Device Table Component
 * Simplified version without react-window for now
 * TODO: Re-implement virtualization with correct react-window v2 API
 * 
 * Features:
 * - Keyboard navigation support
 * - Maintains all table functionality (sorting, filtering, pagination)
 */

import React, { useEffect } from "react";
import { Table, flexRender, ColumnDef } from "@tanstack/react-table";
import { ChevronUp, ChevronDown } from "lucide-react";
import { Device } from "../../types/device";

interface VirtualizedDeviceTableProps {
  data: Device[];
  columns: ColumnDef<Device>[];
  table: Table<Device>;
}

const ROW_HEIGHT = 60; // Height of each row in pixels

const VirtualizedDeviceTable: React.FC<VirtualizedDeviceTableProps> = ({
  data,
  columns,
  table,
}) => {
  const [focusedRowIndex, setFocusedRowIndex] = React.useState<number>(-1);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (focusedRowIndex === -1) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          if (focusedRowIndex < data.length - 1) {
            setFocusedRowIndex(focusedRowIndex + 1);
          }
          break;
        case "ArrowUp":
          e.preventDefault();
          if (focusedRowIndex > 0) {
            setFocusedRowIndex(focusedRowIndex - 1);
          }
          break;
        case "Enter":
          e.preventDefault();
          // Trigger view device action
          const device = data[focusedRowIndex];
          if (device) {
            window.location.href = `/devices/${device.deviceId}`;
          }
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [focusedRowIndex, data]);

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Table Header */}
      <div className="bg-gray-50 dark:bg-gray-700 flex items-center border-b border-gray-200 dark:border-gray-700">
        {table.getHeaderGroups().map((headerGroup) => (
          <div key={headerGroup.id} className="flex w-full" role="row">
            {headerGroup.headers.map((header, index) => (
              <div
                key={header.id}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors flex-1"
                style={{
                  width: `${100 / columns.length}%`,
                  minWidth: index === 0 ? "150px" : "100px",
                }}
                onClick={header.column.getToggleSortingHandler()}
                role="columnheader"
                aria-sort={
                  header.column.getIsSorted()
                    ? header.column.getIsSorted() === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                <div className="flex items-center gap-2">
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {header.column.getIsSorted() && (
                    <span aria-hidden="true">
                      {header.column.getIsSorted() === "asc" ? (
                        <ChevronUp size={14} />
                      ) : (
                        <ChevronDown size={14} />
                      )}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Table Body */}
      <div className="bg-white dark:bg-gray-800 max-h-[600px] overflow-y-auto">
        {table.getRowModel().rows.map((row, index) => {
          const isFocused = index === focusedRowIndex;
          
          return (
            <div
              key={row.id}
              className={`flex items-center border-b border-gray-200 dark:border-gray-700 ${
                isFocused
                  ? "bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-500"
                  : "hover:bg-gray-50 dark:hover:bg-gray-700"
              } transition-colors`}
              style={{ height: `${ROW_HEIGHT}px` }}
              role="row"
              tabIndex={0}
              onFocus={() => setFocusedRowIndex(index)}
              aria-rowindex={index + 1}
            >
              {row.getVisibleCells().map((cell, cellIndex) => (
                <div
                  key={cell.id}
                  className="px-4 py-3 flex-1"
                  style={{
                    width: `${100 / columns.length}%`,
                    minWidth: cellIndex === 0 ? "150px" : "100px",
                  }}
                  role="cell"
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </div>
              ))}
            </div>
          );
        })}
      </div>

      {/* Keyboard navigation hint */}
      <div className="px-4 py-2 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Tip: Use arrow keys to navigate, Enter to view device details
        </p>
      </div>
    </div>
  );
};

export default VirtualizedDeviceTable;
