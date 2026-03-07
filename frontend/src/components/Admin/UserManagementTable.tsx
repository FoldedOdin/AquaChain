/**
 * User Management Table Component
 * Displays all users with management actions using TanStack Table
 * 
 * Features:
 * - Sortable columns (User, Role, Last Login, Status)
 * - Filtering by role and status
 * - Search by user email
 * - Pagination with configurable page sizes
 * - Action buttons (Change Role, Disable User, Reset Password)
 * - Role and status badges
 * - Relative time formatting for Last Login
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.11, 6.13, 6.14
 */

import React, { useState, useEffect, useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  SortingState,
  ColumnDef,
} from "@tanstack/react-table";
import { formatDistanceToNow } from "date-fns";
import { ChevronUp, ChevronDown } from "lucide-react";

import { User, UserFilters } from "../../types/user";
import { useDashboard } from "../../contexts/DashboardContext";
import { MockDataService } from "../../services/mockDataService";
import StatusBadge from "../common/StatusBadge";
import MockDataBadge from "../common/MockDataBadge";
import LoadingSkeleton from "../common/LoadingSkeleton";
import RoleBadge from "./RoleBadge";
import UserActions from "./UserActions";

const UserManagementTable: React.FC = () => {
  const { lastRefreshTimestamp } = useDashboard();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<UserFilters>({
    search: "",
    role: "All",
    status: "All",
  });
  const [sorting, setSorting] = useState<SortingState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 });

  // Load users from mock data service
  useEffect(() => {
    setLoading(true);
    const allUsers = MockDataService.getUsers();
    setUsers(allUsers);
    setLoading(false);
  }, [lastRefreshTimestamp]);

  // Filter users based on search and filter criteria
  const filteredUsers = useMemo(() => {
    return users.filter((user) => {
      // Search filter (debounced in input handler)
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        if (!user.email.toLowerCase().includes(searchLower)) {
          return false;
        }
      }

      // Role filter
      if (filters.role !== "All" && user.role !== filters.role) {
        return false;
      }

      // Status filter
      if (filters.status !== "All" && user.status !== filters.status) {
        return false;
      }

      return true;
    });
  }, [users, filters]);

  // Define table columns
  const columns = useMemo<ColumnDef<User>[]>(
    () => [
      {
        accessorKey: "email",
        header: "User",
        cell: ({ row }) => (
          <span className="text-sm text-gray-900 dark:text-white">
            {row.original.email}
          </span>
        ),
      },
      {
        accessorKey: "role",
        header: "Role",
        cell: ({ row }) => <RoleBadge role={row.original.role} />,
        sortingFn: (rowA, rowB) => {
          // Numeric sorting: Admin=3, Technician=2, Consumer=1
          const roleValues = { Admin: 3, Technician: 2, Consumer: 1 };
          return roleValues[rowA.original.role] - roleValues[rowB.original.role];
        },
      },
      {
        accessorKey: "lastLogin",
        header: "Last Login",
        cell: ({ row }) => (
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {formatDistanceToNow(row.original.lastLogin, { addSuffix: true })}
          </span>
        ),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <StatusBadge status={row.original.status} />,
        sortingFn: (rowA, rowB) => {
          // Numeric sorting: Active=2, Inactive=1
          const statusValues = { Active: 2, Inactive: 1 };
          return statusValues[rowA.original.status] - statusValues[rowB.original.status];
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: ({ row }) => <UserActions user={row.original} />,
      },
    ],
    []
  );

  // Initialize TanStack Table
  const table = useReactTable({
    data: filteredUsers,
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  // Debounced search handler
  const handleSearchChange = useMemo(() => {
    let timeoutId: NodeJS.Timeout;
    return (value: string) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        setFilters((prev) => ({ ...prev, search: value }));
        setPagination((prev) => ({ ...prev, pageIndex: 0 })); // Reset to first page
      }, 300);
    };
  }, []);

  // Clear all filters
  const handleClearFilters = () => {
    setFilters({ search: "", role: "All", status: "All" });
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  };

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.role !== "All") count++;
    if (filters.status !== "All") count++;
    return count;
  }, [filters]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <LoadingSkeleton count={10} />
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          User Management
        </h2>
        <MockDataBadge />
      </div>

      {/* Table Toolbar */}
      <div className="flex items-center gap-4 mb-4 flex-wrap">
        <input
          type="text"
          placeholder="Search by email..."
          defaultValue={filters.search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          aria-label="Search users"
        />

        <select
          value={filters.role}
          onChange={(e) => {
            setFilters((prev) => ({ ...prev, role: e.target.value as any }));
            setPagination((prev) => ({ ...prev, pageIndex: 0 }));
          }}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          aria-label="Filter by role"
        >
          <option value="All">All Roles</option>
          <option value="Admin">Admin</option>
          <option value="Technician">Technician</option>
          <option value="Consumer">Consumer</option>
        </select>

        <select
          value={filters.status}
          onChange={(e) => {
            setFilters((prev) => ({ ...prev, status: e.target.value as any }));
            setPagination((prev) => ({ ...prev, pageIndex: 0 }));
          }}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          aria-label="Filter by status"
        >
          <option value="All">All Status</option>
          <option value="Active">Active</option>
          <option value="Inactive">Inactive</option>
        </select>

        <button
          onClick={handleClearFilters}
          className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          aria-label="Clear all filters"
        >
          Clear Filters
          {activeFilterCount > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full" role="table">
          <thead className="bg-gray-50 dark:bg-gray-700">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} role="row">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
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
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
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
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-gray-500 dark:text-gray-400"
                >
                  No users found matching the current filters.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  role="row"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="px-4 py-3 whitespace-nowrap"
                      role="cell"
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4 flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Showing{" "}
            {table.getState().pagination.pageIndex *
              table.getState().pagination.pageSize +
              1}{" "}
            to{" "}
            {Math.min(
              (table.getState().pagination.pageIndex + 1) *
                table.getState().pagination.pageSize,
              filteredUsers.length
            )}{" "}
            of {filteredUsers.length} users
          </div>

          <select
            value={table.getState().pagination.pageSize}
            onChange={(e) => {
              table.setPageSize(Number(e.target.value));
            }}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            aria-label="Rows per page"
          >
            <option value={10}>10 per page</option>
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-900 dark:text-white"
            aria-label="Previous page"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount()}
          </span>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-900 dark:text-white"
            aria-label="Next page"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserManagementTable;
