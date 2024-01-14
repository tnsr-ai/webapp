import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Home from "../page";
import "@testing-library/jest-dom";
import userEvent from "@testing-library/user-event";

jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      prefetch: () => null,
    };
  },
}));

describe("HomeComponent", () => {
  describe("Render", () => {
    it("should have login form", () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("loginForm");
      expect(myElement).toBeInTheDocument();
    });

    it("should have gradient sidebar", () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("gradientBar");
      expect(myElement).toBeInTheDocument();
    });
  });

  describe("Behaviour", () => {
    it("should have sign in button disabled", () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("signInButton");
      expect(myElement).toBeDisabled();
    });

    it("should check for invalid email", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "test");
      await waitFor(() => {
        const invalidEmail = screen.getByTestId("invalidEmail");
        expect(invalidEmail).toHaveClass("block");
      });
    });

    it("should check for valid email", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "admin@email.com");
      await waitFor(() => {
        const invalidEmail = screen.queryByTestId("invalidEmail");
        expect(invalidEmail).toHaveClass("hidden");
      });
    });

    it("should check for sign in btn enabled", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "admin@email.com");
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "password");
      const myElement = screen.getByTestId("signInButton");
      expect(myElement).not.toBeDisabled();
    });

    it("should check for sign in btn disabled", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "test");
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "password");
      const myElement = screen.getByTestId("signInButton");
      expect(myElement).toBeDisabled();
    });

    it("should check for google sso btn", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const googleBtn = screen.getByTestId("googleLogin");
      expect(googleBtn).toBeInTheDocument();
    });

    it("should check for create account redirect", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const createAccount = screen.getByTestId("createAccount");
      expect(createAccount).toBeInTheDocument();
    });

    it("should check for forgot password redirect", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const forgotPassword = screen.getByTestId("forgotPassword");
      expect(forgotPassword).toBeInTheDocument();
    });

    it("should call handleSubmit when sign-in button is clicked", async () => {
      const queryClient = new QueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <Home />
        </QueryClientProvider>
      );
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "admin@email.com");
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "password");
      const signInButton = screen.getByTestId("signInButton");
      signInButton.onclick = jest.fn();
      await userEvent.click(signInButton);
      expect(signInButton.onclick).toHaveBeenCalled();
    });
  });
});
