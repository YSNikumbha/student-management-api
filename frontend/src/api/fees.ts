import { apiRequest } from "./client";
import type { FeeFormInput, FeesData, PaymentFormInput } from "../types";

export function getFeesData(): Promise<FeesData> {
  return apiRequest<FeesData>("/ui/fees");
}

export function createFee(data: FeeFormInput) {
  return apiRequest("/fees", { method: "POST", json: data });
}

export function updateFee(id: number, data: Partial<FeeFormInput>) {
  return apiRequest(`/fees/${id}`, { method: "PUT", json: data });
}

export function deleteFee(id: number) {
  return apiRequest<void>(`/fees/${id}`, { method: "DELETE" });
}

export function recordPayment(feeId: number, data: PaymentFormInput) {
  return apiRequest(`/fees/${feeId}/payments`, { method: "POST", json: data });
}
