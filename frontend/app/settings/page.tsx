"use client";
import { Loader } from "@mantine/core";
import AppBar from "../components/AppBar";
import SideDrawer from "../components/SideDrawer";
import SettingsTab from "./SettingsTab";
import { useGetSettings } from "../api/index";
import Error from "../components/ErrorTab";

export default function Settings() {
  const { data, isLoading, isSuccess, isError } = useGetSettings();
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
      <div className="mt-5">
        <div className="lg:col-start-2 lg:col-end-3 lg:row-start-2 mt-5 mb-10">
          {isLoading && (
            <div className="w-full h-full flex justify-center items-center">
              <Loader color="grape" variant="bars" />
            </div>
          )}
          {isSuccess && <SettingsTab data={data} />}
          {isError && <Error />}
        </div>
      </div>
    </div>
  );
}
