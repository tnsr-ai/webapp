/* eslint-disable */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import InvoiceTable from "../InvoiceTable";
import { useGetInvoice } from "../../api/index";
import { getCookie } from "cookies-next";
import { toast } from "sonner";

jest.mock("../../api/index", () => ({
  useGetInvoice: jest.fn(),
}));

jest.mock("cookies-next", () => ({
  getCookie: jest.fn(),
}));

jest.mock("sonner", () => ({
  Toaster: jest.fn(),
  toast: Object.assign(jest.fn(), {
    success: jest.fn(),
    error: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    status: 200,
    blob: () => Promise.resolve(new Blob()),
  })
) as jest.Mock;

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const wrapper = ({ children }: { children: any }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
);

describe("InvoiceTable", () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    (useGetInvoice as jest.Mock).mockReturnValue({
      data: {
        data: [
          {
            orderID: 123,
            date: "2021-01-01",
            payment_details: {
              card: "visa",
              last4: "1234",
            },
            currency: "USD",
            amount: "100",
            status: "Completed",
          },
        ],
        total: 1,
      },
      isLoading: false,
      isSuccess: true,
      isError: false,
      refetch: jest.fn(),
    });
    (getCookie as jest.Mock).mockReturnValue("fake-jwt-token");
  });

  it("renders successfully with invoices", () => {
    render(<InvoiceTable />, { wrapper });

    expect(screen.getByText("Invoices")).toBeInTheDocument();
    expect(screen.getByText("#1123")).toBeInTheDocument();
    expect(screen.getByText("USD 100")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useGetInvoice as jest.Mock).mockReturnValueOnce({
      isLoading: true,
      isSuccess: false,
      isError: false,
      data: undefined,
      refetch: jest.fn(),
    });
    render(<InvoiceTable />, { wrapper });

    const loader = screen.findByRole("progressbar");
    expect(loader).toBeTruthy();
  });

  it("shows error state", () => {
    (useGetInvoice as jest.Mock).mockReturnValueOnce({
      isError: true,
    });
    render(<InvoiceTable />, { wrapper });

    expect(
      screen.getByText("Unable to fetch invoice data")
    ).toBeInTheDocument();
  });

  // Additional tests can be added as needed
});
