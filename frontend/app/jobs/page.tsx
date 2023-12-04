import AppBar from "../components/AppBar";
import SideDrawer from "../components/SideDrawer";
import JobsTable from "./JobsTable";

export default function Dashboard() {

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] grid-rows-[minmax(62px,_90px)_1fr]">
      <div className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-span-2 hidden lg:block">
        <div className="fixed top-0 h-full">
          <SideDrawer />
        </div>
      </div>
      <div className="sticky top-0">
        <AppBar />
      </div>
      <div className="">
        <div className="max-w-[1500px] m-auto">
          <JobsTable />
        </div>
      </div>
    </div>
  );
}
