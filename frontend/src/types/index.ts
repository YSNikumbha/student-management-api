export type Role = "admin" | "teacher" | "accountant" | "staff";

export type User = {
  id: number;
  name: string;
  email: string;
  role: Role | string;
  role_id?: number | null;
  role_display_name?: string | null;
  permissions?: string[];
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages?: number;
};

export type StudentStatus = "active" | "inactive" | "transferred";
export type FeeStatus = "paid" | "partial" | "overdue" | "pending" | "unpaid";
export type AttendanceStatus = "present" | "absent" | "late" | "excused";

export type StudentRow = {
  id: number;
  rollNo: string;
  name: string;
  avatar?: string | null;
  email: string;
  phone?: string | null;
  classId?: number | null;
  className?: string | null;
  section?: string | null;
  gender?: string | null;
  dob?: string | null;
  address?: string | null;
  parentName?: string | null;
  parentPhone?: string | null;
  enrolledDate?: string | null;
  status: StudentStatus | string;
  bloodGroup?: string | null;
  feeStatus: FeeStatus | string;
  gpa: number;
  percentage?: number;
  grade?: string;
  courseId?: number | null;
};

export type StudentFormInput = {
  student_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  date_of_birth?: string | null;
  profile_photo?: string | null;
  gender?: string | null;
  address?: string | null;
  parent_name?: string | null;
  parent_phone?: string | null;
  blood_group?: string | null;
  course_id?: number | null;
  academic_year_id?: number | null;
  semester_id?: number | null;
  batch_id?: number | null;
  admission_date?: string | null;
  status?: StudentStatus;
};

export type StudentsData = {
  summary: {
    total_students: number;
    active: number;
    fee_overdue: number;
    avg_gpa: number;
  };
  items: StudentRow[];
};

export type ClassRoom = {
  id: number;
  name: string;
  program?: string | null;
  grade?: string | null;
  section?: string | null;
  teacher?: string | null;
  class_teacher_id?: number | null;
  student_count: number;
  average_gpa: number;
  room?: string | null;
  schedule?: string | null;
  course_id: number;
  academic_year_id: number;
  semester_id?: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ClassFormInput = {
  name: string;
  course_id: number;
  academic_year_id: number;
  semester_id?: number | null;
  class_teacher_id?: number | null;
  section?: string | null;
  capacity?: number | null;
  room?: string | null;
  schedule?: string | null;
  is_active?: boolean;
};

export type ClassesData = {
  summary: {
    total_classes: number;
    total_students: number;
    grade_levels: number;
    avg_class_size: number;
  };
  items: ClassRoom[];
};

export type ChartMonth = {
  month: string;
  present?: number;
  absent?: number;
  late?: number;
  excused?: number;
  collected?: number;
  pending?: number;
};

export type ReportPeriod = "daily" | "monthly" | "yearly" | "custom";

export type ReportFilters = {
  period?: ReportPeriod | "";
  date?: string;
  month?: number | "";
  year?: number | "";
  from_date?: string;
  to_date?: string;
  class_id?: number | "";
  student_id?: number | "";
  subject_id?: number | "";
  category_id?: number | "";
  attendance_status?: AttendanceStatus | "";
  fee_status?: FeeStatus | "";
  top_n?: 5 | 10 | 20;
};

export type DashboardData = {
  kpis: {
    total_students: number;
    attendance_rate: number;
    fee_collection: number;
    outstanding_dues: number;
  };
  attendance_overview: ChartMonth[];
  fee_collection: ChartMonth[];
  recent_enrollments: StudentRow[];
  grade_distribution: { grade?: string; range?: string; count: number; color?: string }[];
  quick_stats: {
    total_classes: number;
    fee_collection_rate: number;
    avg_attendance: number;
    active_students: number;
  };
};

export type AttendanceRecordRow = {
  id: number;
  studentId: number;
  studentName: string;
  rollNo: string;
  date: string;
  status: AttendanceStatus | string;
  classId?: number | null;
  className?: string | null;
  note?: string | null;
};

export type AttendanceData = {
  date: string;
  classes: ClassRoom[];
  records: AttendanceRecordRow[];
  summary: Record<AttendanceStatus, number>;
  trends: ChartMonth[];
};

export type FeeRecord = {
  id: number;
  student_id: number;
  invoice_number?: string | null;
  student_code?: string | null;
  student_name?: string | null;
  course_id?: number | null;
  title: string;
  fee_type?: string | null;
  total_amount: number | string;
  paid_amount: number | string;
  balance: number | string;
  due_date: string;
  status: FeeStatus | string;
  payment_method?: string | null;
  paid_date?: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
};

export type FeeFormInput = {
  student_id: number;
  title: string;
  total_amount: number;
  due_date: string;
  description?: string | null;
};

export type PaymentFormInput = {
  amount: number;
  payment_date: string;
  payment_method: "cash" | "bank_transfer" | "online" | "cheque";
  reference_number?: string | null;
  notes?: string | null;
};

export type FeesData = {
  summary: {
    total_billed: number;
    collected: number;
    outstanding: number;
    collection_rate: number;
  };
  records: FeeRecord[];
  fee_collection: ChartMonth[];
};

export type ReportsData = {
  academic: {
    summary: {
      avg_school_gpa: number;
      top_gpa: number;
      pass_rate: number;
      honor_roll: number;
    };
    subject_performance: { subject: string; avg: number; highest: number; lowest: number }[];
    subject_radar?: { subject: string; score: number }[];
    gpa_distribution: { range: string; count: number }[];
    class_average_gpa: { class: string; avgGpa: number }[];
    top_performers?: StudentRow[];
    top_students?: {
      student_id: number;
      student_name: string;
      student_code: string;
      class_name?: string | null;
      gpa: number;
      percentage: number;
    }[];
    needs_attention: StudentRow[];
  };
  attendance: {
    summary: {
      avg_attendance_rate: number;
      perfect_attendance: number;
      chronic_absentees: number;
      late_arrivals_avg: number;
      present?: number;
      absent?: number;
      late?: number;
      excused?: number;
    };
    monthly: ChartMonth[];
    rows?: Array<{
      date?: string | null;
      student_id?: number;
      student_code: string;
      student_name: string;
      course_name?: string | null;
      status?: string;
      total_marked_days?: number;
      present_days?: number;
      absent_days?: number;
      late_days?: number;
      excused_days?: number;
      attendance_percentage?: number;
    }>;
  };
  finance: FeesData & {
    summary: FeesData["summary"] & {
      paid_count?: number;
      partial_count?: number;
      overdue_count?: number;
      date_basis?: string;
    };
  };
  filter_options?: {
    classes: ClassRoom[];
    students: Array<{ id: number; name: string; student_code: string; class_id?: number | null }>;
    subjects: Array<{ id: number; name: string; code: string; course_id: number; semester_id: number }>;
    fee_categories: Array<{ id: number; name: string; is_active: boolean }>;
  };
};

export type SystemSettings = {
  id: number;
  school_name: string;
  official_email?: string | null;
  phone?: string | null;
  address?: string | null;
  logo_path?: string | null;
  default_academic_year_id?: number | null;
  currency: string;
  timezone: string;
  language: string;
  created_at: string;
  updated_at: string;
};

export type NotificationPreference = {
  id: number;
  user_id: number;
  fee_alerts: boolean;
  attendance_alerts: boolean;
  system_notifications: boolean;
  created_at: string;
  updated_at: string;
};

export type AcademicYear = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
};

export type Course = {
  id: number;
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
};

export type Semester = {
  id: number;
  name: string;
  course_id: number;
  academic_year_id: number;
  semester_number: number;
  is_active: boolean;
};

export type FeeCategory = {
  id: number;
  name: string;
  description?: string | null;
  is_active: boolean;
};

export type FeeStructure = {
  id: number;
  name: string;
  course_id: number;
  course_name?: string | null;
  academic_year_id: number;
  academic_year_name?: string | null;
  semester_id?: number | null;
  semester_name?: string | null;
  category_id: number;
  category_name?: string | null;
  total_amount: number | string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  assignment_count?: number;
};

export type UserFormInput = {
  name: string;
  email: string;
  role: Role | string;
  role_id?: number | null;
  password?: string;
  is_active?: boolean;
};

export type Permission = {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  module: string;
  created_at: string;
};

export type RoleRecord = {
  id: number;
  name: string;
  display_name: string;
  description?: string | null;
  is_system: boolean;
  is_active: boolean;
  user_count: number;
  permission_codes: string[];
  created_at: string;
  updated_at: string;
};

export type RolesPermissionsData = {
  roles: RoleRecord[];
  permissions: Permission[];
};

export type SearchResult = {
  id: number;
  title: string;
  subtitle?: string | null;
  type: string;
  url: string;
};

export type SearchResponse = {
  students: SearchResult[];
  courses: SearchResult[];
  subjects: SearchResult[];
  batches: SearchResult[];
  users: SearchResult[];
};

export type NotificationItem = {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
  read_at?: string | null;
};
