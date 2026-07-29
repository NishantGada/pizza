import React from "react";
import ReactDOM from "react-dom/client";
import { Provider as UrqlProvider } from "urql";

import App from "./App";
import "./index.css";
import { client } from "./lib/graphql";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <UrqlProvider value={client}>
      <App />
    </UrqlProvider>
  </React.StrictMode>,
);
