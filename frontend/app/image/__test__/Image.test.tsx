import { render, screen } from "@testing-library/react";
import Image from "../page";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

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

jest.mock("../../components/AppBar", () => {
  const AppBarMock = () => <div data-testid="appBar">AppBar Mock</div>;
  AppBarMock.displayName = "AppBarMock";
  return AppBarMock;
});

jest.mock("../../components/SideDrawer", () => {
  const SideDrawerMock = () => (
    <div data-testid="sideDrawer">SideDrawer Mock</div>
  );
  SideDrawerMock.displayName = "SideDrawerMock";
  return SideDrawerMock;
});

jest.mock("../../components/DropZone", () => {
  const DropZoneMock = ({
    filetype,
    acceptedtype,
    maxFileSize,
  }: {
    filetype: any;
    acceptedtype: any;
    maxFileSize: any;
  }) => {
    const acceptedTypesString = Object.keys(acceptedtype).join(", ");
    return (
      <div data-testid="dropZone">
        DropZone Mock - {filetype}, {acceptedTypesString}, {maxFileSize}
      </div>
    );
  };
  DropZoneMock.displayName = "DropZoneMock";
  return DropZoneMock;
});

jest.mock("../../content/contentCards/ContentList", () => {
  const ContentListMock = ({ VideoUpload }: { VideoUpload: any }) => (
    <div data-testid="contentList">
      ContentList Mock - Upload State: {VideoUpload ? "true" : "false"}
    </div>
  );
  ContentListMock.displayName = "ContentListMock";
  return ContentListMock;
});

describe("VideoComponent", () => {
  describe("Render", () => {
    it("renders AppBar, SideDrawer, DropZone, and ContentList components", () => {
      render(<Image />);

      expect(screen.getByTestId("appBar")).toBeInTheDocument();
      expect(screen.getByTestId("sideDrawer")).toBeInTheDocument();
      expect(screen.getByTestId("dropZone")).toBeInTheDocument();
      expect(screen.getByTestId("contentList")).toBeInTheDocument();
    });
  });
});
