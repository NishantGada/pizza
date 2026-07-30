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

export const CONTRIBUTION_CATEGORIES = gql`
  query ContributionCategories {
    contributionCategories {
      id
      name
      kind
      value
      createdAt
    }
  }
`;

export const ADD_CONTRIBUTION_CATEGORY = gql`
  mutation AddContributionCategory($name: String!, $kind: CategoryKind!, $value: Decimal!) {
    addContributionCategory(name: $name, kind: $kind, value: $value) {
      id
      name
      kind
      value
    }
  }
`;

export const UPDATE_CONTRIBUTION_CATEGORY = gql`
  mutation UpdateContributionCategory(
    $id: UUID!
    $name: String
    $kind: CategoryKind
    $value: Decimal
  ) {
    updateContributionCategory(id: $id, name: $name, kind: $kind, value: $value) {
      id
      name
      kind
      value
    }
  }
`;

export const DELETE_CONTRIBUTION_CATEGORY = gql`
  mutation DeleteContributionCategory($id: UUID!) {
    deleteContributionCategory(id: $id)
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
    contributionCategoryId
    name
    kind
    value
    amount
    source
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
      projectionLabel
      savedProjection { actual annual relative }
      retirementProjection { actual annual relative }
      hsaProjection { actual annual relative }
      allocatedProjection { actual annual relative }
      byCategory {
        name
        cycleCount
        projection { actual annual relative }
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

export const SET_CYCLE_CATEGORY = gql`
  mutation SetCycleCategory(
    $payCycleId: UUID!
    $contributionCategoryId: UUID!
    $kind: CategoryKind!
    $value: Decimal!
  ) {
    setCycleCategory(
      payCycleId: $payCycleId
      contributionCategoryId: $contributionCategoryId
      kind: $kind
      value: $value
    ) {
      ${CYCLE_FIELDS}
    }
  }
`;

export const RESET_CYCLE_CATEGORY = gql`
  mutation ResetCycleCategory($payCycleId: UUID!, $contributionCategoryId: UUID!) {
    resetCycleCategory(payCycleId: $payCycleId, contributionCategoryId: $contributionCategoryId) {
      ${CYCLE_FIELDS}
    }
  }
`;

export const ADD_CYCLE_CATEGORY = gql`
  mutation AddCycleCategory(
    $payCycleId: UUID!
    $name: String!
    $kind: CategoryKind!
    $value: Decimal!
  ) {
    addCycleCategory(payCycleId: $payCycleId, name: $name, kind: $kind, value: $value) {
      ${CYCLE_FIELDS}
    }
  }
`;

export const UPDATE_CYCLE_CATEGORY = gql`
  mutation UpdateCycleCategory($id: UUID!, $name: String, $kind: CategoryKind, $value: Decimal) {
    updateCycleCategory(id: $id, name: $name, kind: $kind, value: $value) {
      ${CYCLE_FIELDS}
    }
  }
`;

export const DELETE_CYCLE_CATEGORY = gql`
  mutation DeleteCycleCategory($id: UUID!) {
    deleteCycleCategory(id: $id) {
      ${CYCLE_FIELDS}
    }
  }
`;
