import { render, screen, waitFor } from "@testing-library/react";
import Forgot from "../page";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import fetchMock from "jest-fetch-mock";

jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      prefetch: () => null,
    };
  },
}));

fetchMock.enableMocks();

const queryClient = new QueryClient();

describe("ForgotComponent", () => {
  beforeEach(() => {
    fetchMock.resetMocks();
  });
  describe("Render", () => {
    it("should have forgot form", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Forgot />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("forgotForm");
      expect(myElement).toBeInTheDocument();
    });

    it("should have email input", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Forgot />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("emailInput");
      expect(myElement).toBeInTheDocument();
    });
  });

  describe("Behaviour", () => {
    it("enables the reset button when all fields are valid", async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Forgot />
        </QueryClientProvider>
      );
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "admin@tnsr.ai");
      const resetButton = screen.getByTestId("resetPasswordButton");
      expect(resetButton).toBeEnabled();
    });

    it("enables the reset button and submit fn is called", async () => {
      fetchMock.mockResponseOnce(
        JSON.stringify({
          detail: "Success",
          data: "Password reset link sent to your email.",
        })
      );
      render(
        <QueryClientProvider client={queryClient}>
          <Forgot />
        </QueryClientProvider>
      );
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "admin@tnsr.ai");
      const resetButton = screen.getByTestId("resetPasswordButton");
      resetButton.onclick = jest.fn();
      await userEvent.click(resetButton);
      await screen.findByText("Password reset link sent to your email.");
      expect(fetchMock).toHaveBeenCalled();
    });
  });
});
