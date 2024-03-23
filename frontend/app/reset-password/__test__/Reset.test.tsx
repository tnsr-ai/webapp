import { render, screen, waitFor } from "@testing-library/react";
import Reset from "../page";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import fetchMock from "jest-fetch-mock";

jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      prefetch: () => null,
    };
  },
}));

fetchMock.enableMocks();

jest.mock("next/navigation", () => ({
  useSearchParams: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  useSearchParams: () => {
    return new URLSearchParams({
      user_id: "1",
      password_token: "token",
    });
  },
}));

const queryClient = new QueryClient();

describe("ForgotComponent", () => {
  beforeEach(() => {
    fetchMock.resetMocks();
  });
  describe("Render", () => {
    it("should have reset form", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Reset />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("resetForm");
      expect(myElement).toBeInTheDocument();
    });

    it("should have email input", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Reset />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("passwordInput");
      const myElement2 = screen.getByTestId("confirmPasswordInput");
      expect(myElement).toBeInTheDocument();
      expect(myElement2).toBeInTheDocument();
    });
  });

  describe("Behaviour", () => {
    it("enables the reset button when all fields are valid", async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Reset />
        </QueryClientProvider>
      );
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "password");
      const confirmPasswordInput = screen.getByTestId("confirmPasswordInput");
      await userEvent.type(confirmPasswordInput, "password");
      const resetButton = screen.getByTestId("resetPasswordButton");
      expect(resetButton).toBeEnabled();
    });

    it("enables the reset button and submit fn is called", async () => {
      fetchMock.mockResponseOnce(
        JSON.stringify({
          detail: "Success",
          data: "Password reset successfully",
        })
      );
      render(
        <QueryClientProvider client={queryClient}>
          <Reset />
        </QueryClientProvider>
      );
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "password");
      const confirmPasswordInput = screen.getByTestId("confirmPasswordInput");
      await userEvent.type(confirmPasswordInput, "password");
      const resetButton = screen.getByTestId("resetPasswordButton");
      resetButton.onclick = jest.fn();
      await userEvent.click(resetButton);
      await screen.findByText("Password changed successfully.");
      expect(fetchMock).toHaveBeenCalled();
    });
  });
});
