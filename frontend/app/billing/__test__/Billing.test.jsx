import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useGetBalance, useGetIP } from "../../api/index";
import Billing from "../page";
import BillingContent from "../BillingContent";
import { Toaster } from "sonner";

// Mock the API hooks and external components
jest.mock("../../api/index", () => ({
  useGetBalance: jest.fn(),
  useGetIP: jest.fn(),
}));

jest.mock("../../components/AppBar", () => () => <div>AppBar</div>);
jest.mock("../../components/SideDrawer", () => () => <div>SideDrawer</div>);
jest.mock("../BillingContent", () => () => <div>BillingContent</div>);
jest.mock("../PricingTab", () => () => <div>PricingTab</div>);
jest.mock("../InvoiceTable", () => () => <div>InvoiceTable</div>);
jest.mock("../../components/ErrorTab", () => () => <div>ErrorTab</div>);
jest.mock("@mantine/core", () => ({
  Loader: () => <div>Loader</div>,
}));

jest.mock("next/navigation", () => ({
  useSearchParams: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  useSearchParams: () => {
    return new URLSearchParams({
      payment_status: "success",
      token: "12345",
    });
  },
}));

jest.mock("sonner", () => ({
  Toaster: jest.fn(),
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe("Billing Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render loading state", () => {
    useGetBalance.mockReturnValue({
      data: null,
      isLoading: true,
      isSuccess: false,
      isError: false,
    });

    useGetIP.mockReturnValue({
      data: null,
      isSuccess: false,
      isError: false,
      refetch: jest.fn(),
    });

    render(<Billing />);

    expect(screen.getByText("Loader")).toBeInTheDocument();
  });

  it("should render success state with data", async () => {
    useGetBalance.mockReturnValue({
      data: { detail: "Success" },
      isLoading: false,
      isSuccess: true,
      isError: false,
    });
    useGetIP.mockReturnValue({
      data: { country: "IN" },
      isSuccess: true,
      isError: false,
      refetch: jest.fn(),
    });

    render(<Billing />);

    await waitFor(() => {
      expect(screen.getByText("BillingContent")).toBeInTheDocument();
      expect(screen.getByText("PricingTab")).toBeInTheDocument();
      expect(screen.getByText("InvoiceTable")).toBeInTheDocument();
    });
  });

  it("should render error state", () => {
    useGetBalance.mockReturnValue({
      data: null,
      isLoading: false,
      isSuccess: false,
      isError: true,
    });

    render(<Billing />);

    expect(screen.getByText("ErrorTab")).toBeInTheDocument();
  });
});
