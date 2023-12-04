import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Register from "../page";
import "@testing-library/jest-dom";

jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      prefetch: () => null,
    };
  },
}));

describe("RegisterComponent", () => {
  describe("Render", () => {
    it("should have register form", () => {
      render(<Register />);
      const myElement = screen.getByTestId("registerForm");
      expect(myElement).toBeInTheDocument();
    });
  });
  describe("Behaviour", () => {
    it("enables the sign-up button when all fields are valid", async () => {
      render(<Register />);
      const firstNameInput = screen.getByTestId("firstNameInput");
      await userEvent.type(firstNameInput, "John");
      const lastNameInput = screen.getByTestId("lastNameInput");
      await userEvent.type(lastNameInput, "Doe");
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "john.doe@example.com");
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "Str0ngP@ss!");
      const confirmPasswordInput = screen.getByTestId("confirmPasswordInput");
      await userEvent.type(confirmPasswordInput, "Str0ngP@ss!");
      await waitFor(() => {
        expect(screen.getByTestId("signUpButton")).toBeEnabled();
      });
    });

    it("disables the sign-up button when the first name is space", async () => {
      render(<Register />);
      const firstNameInput = screen.getByTestId("firstNameInput");
      await userEvent.type(firstNameInput, " ");
      const lastNameInput = screen.getByTestId("lastNameInput");
      await userEvent.type(lastNameInput, "Doe");
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "john.doe@example.com");
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "Str0ngP@ss!");
      const confirmPasswordInput = screen.getByTestId("confirmPasswordInput");
      await userEvent.type(confirmPasswordInput, "Str0ngP@ss!");
      await waitFor(() => {
        expect(screen.getByTestId("signUpButton")).toBeDisabled();
      });
    });

    it("disables the sign-up button when the email format is incorrect", async () => {
      render(<Register />);
      const firstNameInput = screen.getByTestId("firstNameInput");
      await userEvent.type(firstNameInput, "Joe");
      const lastNameInput = screen.getByTestId("lastNameInput");
      await userEvent.type(lastNameInput, "Doe");
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "john.doeexample.com");
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "Str0ngP@ss!");
      const confirmPasswordInput = screen.getByTestId("confirmPasswordInput");
      await userEvent.type(confirmPasswordInput, "Str0ngP@ss!");
      await waitFor(() => {
        expect(screen.getByTestId("signUpButton")).toBeDisabled();
      });
    });
  });

  describe("Action", () => {
    it("should submit the form", async () => {
      render(<Register />);
      const firstNameInput = screen.getByTestId("firstNameInput");
      await userEvent.type(firstNameInput, "Joe");
      const lastNameInput = screen.getByTestId("lastNameInput");
      await userEvent.type(lastNameInput, "Doe");
      const emailInput = screen.getByTestId("emailInput");
      await userEvent.type(emailInput, "john.doe@example.com");
      const passwordInput = screen.getByTestId("passwordInput");
      await userEvent.type(passwordInput, "Str0ngP@ss!");
      const confirmPasswordInput = screen.getByTestId("confirmPasswordInput");
      await userEvent.type(confirmPasswordInput, "Str0ngP@ss!");
      const signUpButton = screen.getByTestId("signUpButton");
      signUpButton.onclick = jest.fn();
      await userEvent.click(signUpButton);
      expect(signUpButton.onclick).toHaveBeenCalled();
    });

    it("should check for google sign in sso", async () => {
      render(<Register />);
      const googleBtn = screen.getByTestId("googleLogin");
      expect(googleBtn).toBeInTheDocument();
    });
  });
});
