import { render, screen } from "@testing-library/react";
import Dashboard from "../page";
import DashboardContent from "../dashboard";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { dashboardStats, networkStats } from "../../constants/constants";

jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      prefetch: () => null,
    };
  },
}));

jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => {
    return <img {...props} />;
  },
}));

jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      route: "/",
      pathname: "/",
      query: {},
      asPath: "/",
      prefetch: () => null,
    };
  },
  usePathname: () => "/",
}));

jest.mock("../pieChart", () => {
  const pieChart = () => <div data-testid="pieChart">pieChart Mock</div>;
  pieChart.displayName = "pieChart";
  return pieChart;
});

type DashboardData = {
  user_id: number;
  video_processed: number;
  audio_processed: number;
  image_processed: number;
  downloads: string;
  uploads: string;
  storage_used: number;
  storage_limit: number;
  gpu_usage: string;
  storage_json: string;
  created_at: number;
  updated_at: number;
  name: string;
  balance: number;
  storage: string;
};

type MockDataType = {
  detail: string;
  data: DashboardData;
  verified: boolean;
};

const mockData: MockDataType = {
  detail: "Success",
  data: {
    user_id: 1,
    video_processed: 3,
    audio_processed: 1,
    image_processed: 2,
    downloads: "94.44 MB",
    uploads: "197.80 MB",
    storage_used: 103618301,
    storage_limit: 2147483648,
    gpu_usage: "0 Min",
    storage_json:
      '{"video": 188.86, "audio": 0.16, "image": 8.740000000000002}',
    created_at: 1699080282,
    updated_at: 0,
    name: "Amit",
    balance: 0,
    storage: "98.82 MB / 2 GB",
  },
  verified: true,
};

jest.mock("../../api/index", () => ({
  useDashboard: () => ({
    data: mockData,
    isLoading: false,
    isSuccess: true,
    isError: false,
  }),
  useVerifyUser: () => ({
    data: {
      data: {
        id: 1,
        firstname: "Amit",
        lastname: "Bera",
        email: "admin@email.com",
        verified: true,
        token: "jwt_token",
      },
      detail: "Success",
    },
    isLoading: false,
    isSuccess: true,
    isError: false,
  }),
}));

const queryClient = new QueryClient();

describe("DashboardComponent", () => {
  describe("Render", () => {
    it("should have appbar and side drawer", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Dashboard />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("sideDrawer");
      expect(myElement).toBeInTheDocument();
      const myElement2 = screen.getByTestId("appBar");
      expect(myElement2).toBeInTheDocument();
    });

    it("should have dashboard component", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Dashboard />
        </QueryClientProvider>
      );
      const myElement = screen.getByTestId("dashboardContent");
      expect(myElement).toBeInTheDocument();
    });
  });

  describe("Behaviour", () => {
    it("displays a verified welcome message for verified users", () => {
      render(<DashboardContent data={{ ...mockData, verified: true }} />);
      expect(screen.getByText(`Welcome Back! Amit`)).toBeInTheDocument();
    });

    it("displays a regular welcome message for unverified users", () => {
      render(<DashboardContent data={{ ...mockData, verified: false }} />);
      expect(screen.getByText(`Welcome Amit`)).toBeInTheDocument();
    });

    it("displays the correct balance", () => {
      render(<DashboardContent data={mockData} />);
      expect(screen.getByText(/0 credits/)).toBeInTheDocument();
    });

    it("renders all dashboard stats with the correct values", () => {
      render(<DashboardContent data={mockData} />);
      for (const stat of dashboardStats) {
        expect(screen.getByText(stat.name)).toBeInTheDocument();
        expect(
          screen.getByText(
            mockData.data[stat.key as keyof DashboardData].toString()
          )
        ).toBeInTheDocument();
      }
    });

    it("renders all network stats with the correct values", () => {
      render(<DashboardContent data={mockData} />);
      for (const stat of networkStats) {
        expect(screen.getByText(stat.name)).toBeInTheDocument();
        const value = mockData.data[stat.key as keyof DashboardData];
        if (typeof value === "number" || typeof value === "string") {
          expect(screen.getByText(value.toString())).toBeInTheDocument();
        } else {
          throw new Error(
            `The key '${stat.key}' is not a valid property on DashboardData or is not a number/string.`
          );
        }
      }
    });
  });
});
