"use client";
import AppBar from "../components/AppBar";
import SideDrawer from "../components/SideDrawer";
import DashboardContent from "./dashboard";
import { useDashboard } from "../api/index";
import { Loader } from "@mantine/core";
import Error from "../components/ErrorTab";
import VerifyBanner from "../components/VerifyBanner";

export default function Dashboard() {
  const { data, isLoading, isSuccess, isError } = useDashboard();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] grid-rows-[minmax(62px,_90px)_1fr]">
      <head>
        <title>Tnsr.ai - Dashboard</title>
      </head>
      <div className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-span-2 hidden lg:block">
        <div className="fixed top-0 h-full" data-testid="sideDrawer">
          <SideDrawer />
        </div>
      </div>
      <div className="sticky top-0 max-h-screen z-50" data-testid="appBar">
        {isSuccess === true && data.verified === false && <VerifyBanner />}
        <AppBar />
      </div>
      <div className="mt-5">
        {isLoading === true && (
          <div className="flex mt-10 md:mt-5 justify-center">
            <Loader color="grape" variant="bars" />
          </div>
        )}

        {isSuccess === true && data.detail === "Success" && (
          <DashboardContent data={data} />
        )}
        {isError === true && <Error />}
      </div>
    </div>
  );
}
