import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BillingContent from "../BillingContent";

// Mock BuyPrompt component
jest.mock("../../components/ModalComponents/BuyModal", () => {
  const BuyModalMock = (props: any) => (
    <div
      data-testid="buy-prompt"
      className={props.renamePrompt ? "modal-open" : "modal-closed"}
    >
      <button onClick={() => props.setRenamePrompt(false)}>Close Modal</button>
    </div>
  );
  BuyModalMock.displayName = "BuyModalMock";
  return BuyModalMock;
});

describe("BillingContent Component", () => {
  const mockData = {
    detail: "Success",
    data: {
      user_id: 1,
      balance: 100,
      lifetime_usage: 200,
      tier: "Free",
    },
    verified: true,
  };

  it("renders with correct data", () => {
    render(<BillingContent data={mockData} />);
    expect(screen.getByText("Token Balance")).toBeInTheDocument();
    expect(screen.getByText("100 credits")).toBeInTheDocument();
    expect(screen.getByText("200 credits")).toBeInTheDocument();
    expect(screen.getByText("Plan: Free")).toBeInTheDocument();
  });

  it("opens BuyPrompt modal on button click", async () => {
    render(<BillingContent data={mockData} />);
    const buyButton = screen.getByText("Buy Tokens");
    await userEvent.click(buyButton);
    await waitFor(() => {
      expect(screen.getByTestId("buy-prompt")).toHaveClass("modal-open");
    });
  });

  it("closes BuyPrompt modal when close button in modal is clicked", async () => {
    render(<BillingContent data={mockData} />);
    const buyButton = screen.getByText("Buy Tokens");
    await userEvent.click(buyButton);
    // Modal should be open now
    const closeModalButton = screen.getByText("Close Modal");
    await userEvent.click(closeModalButton);
    await waitFor(() => {
      expect(screen.getByTestId("buy-prompt")).toHaveClass("modal-closed");
    });
  });

  // Add more test cases as needed
});
