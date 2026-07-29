import { Client, cacheExchange, fetchExchange } from "urql";

import { getToken } from "./auth";

const url = import.meta.env.VITE_GRAPHQL_URL ?? "http://localhost:8000/graphql";

export const client = new Client({
  url,
  exchanges: [cacheExchange, fetchExchange],
  fetchOptions: () => {
    const token = getToken();
    return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
  },
});
