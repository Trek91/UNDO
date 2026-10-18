const names: Record<string, string> = { full: 'Pay in full', partial: 'Split payment', defer: 'Defer payment', hold: 'Hold for review' }
export const actionName = (id: string | null | undefined) => names[id ?? ''] ?? 'No feasible action'
export const dimensionName: Record<string, string> = {
  receipt_delay_days: 'Receipt delay', receipt_probability: 'Receipt probability', unexpected_expense_paise: 'Additional expense',
  mandatory_due_days: 'Mandatory expense day', proposed_amount_paise: 'Proposed payment', supplier_due_days: 'Supplier deadline',
  partial_days: 'Split remainder extension', penalty_paise: 'Contractual penalty', reserve_paise: 'Desired reserve',
}
