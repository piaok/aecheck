export interface CheckResult {
  id: number;
  input_number: string;
  input_name: string;
  matched_number: string | null;
  matched_name: string | null;
  status: string;
  matched_percentage: number;
  message: string;
}

export interface ValidateResponse {
  results: CheckResult[];
}