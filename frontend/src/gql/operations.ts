import { gql } from "urql";

export const ME = gql`
  query Me {
    me {
      id
      email
      createdAt
    }
  }
`;

export const REGISTER = gql`
  mutation Register($email: String!, $password: String!) {
    register(email: $email, password: $password) {
      token
      user {
        id
        email
      }
    }
  }
`;

export const LOGIN = gql`
  mutation Login($email: String!, $password: String!) {
    login(email: $email, password: $password) {
      token
      user {
        id
        email
      }
    }
  }
`;

export const BUDGET_SETTINGS = gql`
  query BudgetSettings {
    budgetSettings {
      id
      savingsPct
      retirement401kPct
      hsaPerCycle
    }
  }
`;

export const UPDATE_BUDGET_SETTINGS = gql`
  mutation UpdateBudgetSettings(
    $savingsPct: Decimal
    $retirement401kPct: Decimal
    $hsaPerCycle: Decimal
  ) {
    updateBudgetSettings(
      savingsPct: $savingsPct
      retirement401kPct: $retirement401kPct
      hsaPerCycle: $hsaPerCycle
    ) {
      id
      savingsPct
      retirement401kPct
      hsaPerCycle
    }
  }
`;

const CYCLE_FIELDS = `
  id
  startDate
  endDate
  income
  savingsPct
  retirement401kPct
  hsaAmount
  savingsAmount
  retirementAmount
  categoriesTotal
  availableSpending
  categories {
    id
    name
    amount
    createdAt
  }
`;

export const DASHBOARD = gql`
  query Dashboard {
    dashboard {
      cycleCount
      totalIncome
      totalSaved
      totalRetirement
      totalHsa
      totalAllocated
      totalContributed
      totalAvailable
      byCategory {
        name
        total
        cycleCount
      }
    }
    payCycles {
      ${CYCLE_FIELDS}
    }
  }
`;

export const PAY_CYCLE = gql`
  query PayCycle($id: UUID!) {
    payCycle(id: $id) {
      ${CYCLE_FIELDS}
    }
  }
`;

export const CREATE_PAY_CYCLE = gql`
  mutation CreatePayCycle($startDate: Date!, $endDate: Date!, $income: Decimal!) {
    createPayCycle(startDate: $startDate, endDate: $endDate, income: $income) {
      ${CYCLE_FIELDS}
    }
  }
`;

export const UPDATE_PAY_CYCLE = gql`
  mutation UpdatePayCycle($id: UUID!, $startDate: Date, $endDate: Date, $income: Decimal) {
    updatePayCycle(id: $id, startDate: $startDate, endDate: $endDate, income: $income) {
      ${CYCLE_FIELDS}
    }
  }
`;

export const DELETE_PAY_CYCLE = gql`
  mutation DeletePayCycle($id: UUID!) {
    deletePayCycle(id: $id)
  }
`;

export const ADD_CATEGORY = gql`
  mutation AddCategory($payCycleId: UUID!, $name: String!, $amount: Decimal!) {
    addCategory(payCycleId: $payCycleId, name: $name, amount: $amount) {
      id
    }
  }
`;

export const UPDATE_CATEGORY = gql`
  mutation UpdateCategory($id: UUID!, $name: String, $amount: Decimal) {
    updateCategory(id: $id, name: $name, amount: $amount) {
      id
    }
  }
`;

export const DELETE_CATEGORY = gql`
  mutation DeleteCategory($id: UUID!) {
    deleteCategory(id: $id)
  }
`;
