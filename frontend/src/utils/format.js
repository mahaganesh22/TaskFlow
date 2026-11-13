export const STATUS_LABELS = {
  TODO: "To Do",
  IN_PROGRESS: "In Progress",
  DONE: "Done"
};

export const PRIORITY_LABELS = {
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High"
};

export const ACTIVITY_LABELS = {
  TASK_CREATED: "created a task",
  TASK_STATUS_CHANGED: "moved a task",
  TASK_ASSIGNED: "assigned a task",
  COMMENT_ADDED: "commented",
  MEMBER_INVITED: "invited a member",
  MEMBER_JOINED: "joined the project team",
  MEMBER_REMOVED: "removed a member"
};

export function formatDate(value) {
  if (!value) return "—";

  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

export function formatDay(value) {
  if (!value) return "—";

  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric"
  });
}

export function toDateTimeLocal(value) {
  if (!value) return "";

  const date = new Date(value);
  const pad = (n) => String(n).padStart(2, "0");

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function fromDateTimeLocal(value) {
  if (!value) return null;
  return new Date(value).toISOString();
}

export function startOfWeek(date = new Date()) {
  const next = new Date(date);
  const day = next.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  next.setDate(next.getDate() + diff);
  next.setHours(0, 0, 0, 0);
  return next;
}

export function memberName(members, userId) {
  const member = members.find((item) => item.user_id === userId);
  return member?.user?.name || "Unassigned";
}
