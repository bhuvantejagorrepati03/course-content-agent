/**
 * Role Context
 * -----------
 * Stores the currently active role ('faculty' | 'student') and provides
 * helpers to check permissions.  The role is persisted in sessionStorage
 * (cleared when the browser tab closes — ideal for a demo).
 */
import React, { createContext, useContext, useState, useCallback } from 'react';

export type Role = 'faculty' | 'student';

interface RoleContextValue {
  role: Role;
  setRole: (r: Role) => void;
  isFaculty: boolean;
  isStudent: boolean;
  /** Returns true when the action is allowed for the current role. */
  can: (action: Permission) => boolean;
}

/**
 * Granular permissions.
 * All read permissions are available to both roles.
 * Write/manage permissions are faculty-only.
 */
export type Permission =
  | 'view:courses'
  | 'view:courseDetail'
  | 'view:assistant'
  | 'view:textbooks'
  | 'view:mapping'
  | 'view:analytics'
  | 'view:syllabus'       // faculty: full page; student: read-only view
  | 'upload:documents'    // faculty only
  | 'delete:documents'    // faculty only
  | 'manage:content';     // faculty only — any write operation

const FACULTY_PERMISSIONS = new Set<Permission>([
  'view:courses', 'view:courseDetail', 'view:assistant', 'view:textbooks',
  'view:mapping', 'view:analytics', 'view:syllabus',
  'upload:documents', 'delete:documents', 'manage:content',
]);

const STUDENT_PERMISSIONS = new Set<Permission>([
  'view:courses', 'view:courseDetail', 'view:assistant', 'view:textbooks',
  'view:mapping', 'view:analytics',
  // 'view:syllabus' deliberately excluded — students get the access-denied page
]);

const SESSION_KEY = 'courseai_role';

function readPersistedRole(): Role {
  try {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored === 'faculty' || stored === 'student') return stored;
  } catch { /* sessionStorage unavailable */ }
  return 'faculty';
}

const RoleContext = createContext<RoleContextValue | null>(null);

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<Role>(readPersistedRole);

  const setRole = useCallback((r: Role) => {
    setRoleState(r);
    try { sessionStorage.setItem(SESSION_KEY, r); } catch { /* ignore */ }
  }, []);

  const can = useCallback((action: Permission): boolean => {
    const set = role === 'faculty' ? FACULTY_PERMISSIONS : STUDENT_PERMISSIONS;
    return set.has(action);
  }, [role]);

  return (
    <RoleContext.Provider value={{
      role,
      setRole,
      isFaculty: role === 'faculty',
      isStudent: role === 'student',
      can,
    }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const ctx = useContext(RoleContext);
  if (!ctx) throw new Error('useRole must be used within RoleProvider');
  return ctx;
}
