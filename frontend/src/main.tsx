import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Provider as UrqlProvider } from "urql";

import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import "./index.css";
import { client } from "./lib/graphql";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <UrqlProvider value={client}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </UrqlProvider>
  </React.StrictMode>,
);
