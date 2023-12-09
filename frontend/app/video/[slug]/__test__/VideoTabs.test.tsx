import { render, screen } from "@testing-library/react";
import VideoTabs from "../page";
import "@testing-library/jest-dom";

jest.mock("../../../components/AppBar", () => {
  const AppBarMock = () => <div data-testid="appBar">AppBar Mock</div>;
  AppBarMock.displayName = "AppBarMock";
  return AppBarMock;
});

jest.mock("../../../components/SideDrawer", () => {
  const SideDrawerMock = () => (
    <div data-testid="sideDrawer">SideDrawer Mock</div>
  );
  SideDrawerMock.displayName = "SideDrawerMock";
  return SideDrawerMock;
});

jest.mock("../../../content/contentLists/ContentRowList", () => {
  const ContentRowListMock = ({ content_id }: { content_id: number }) => (
    <div data-testid="contentListRow">
      ContentListRow Mock - Content ID: {content_id}
    </div>
  );
  ContentRowListMock.displayName = "ContentRowListMock";
  return ContentRowListMock;
});

describe("VideoTabs Component", () => {
  it("renders AppBar, SideDrawer, and ContentListRow components", () => {
    const params = { slug: "123" };
    render(<VideoTabs params={params} />);

    expect(screen.getByTestId("appBar")).toBeInTheDocument();
    expect(screen.getByTestId("sideDrawer")).toBeInTheDocument();
    expect(screen.getByTestId("contentListRow")).toBeInTheDocument();

    expect(
      screen.getByText("ContentListRow Mock - Content ID: 123")
    ).toBeInTheDocument();
  });
});
