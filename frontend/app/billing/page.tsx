"use client";
import AppBar from "../components/AppBar";
import SideDrawer from "../components/SideDrawer";
import BillingContent from "./BillingContent";
import PricingTab from "./PricingTab";
import InvoiceTable from "./InvoiceTable";
import Error from "../components/ErrorTab";
import { useGetBalance, useGetIP } from "../api/index";
import { Loader } from "@mantine/core";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Toaster, toast } from "sonner";
import { Suspense } from "react";

function getCurrentDimension() {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}

function ShowToast() {
  const searchParams = useSearchParams();
  const paymentStatus = searchParams.get("payment_status");
  const token = searchParams.get("token");
  const [toastStatus, setToastStatus] = useState(false);
  const [screenSize, setScreenSize] = useState({
    width: 0,
    height: 0,
  });

  const showToast = () => {
    if (paymentStatus === "success") {
      toast.success(`Payment Successful for ${token} credits`, {
        action: {
          label: "x",
          onClick: () => {
            null;
          },
        },
      });
    }
    if (paymentStatus === "failed") {
      toast.error(`Payment Failed for ${token} credits`, {
        action: {
          label: "x",
          onClick: () => {
            null;
          },
        },
      });
    }
  };

  useEffect(() => {
    if (screenSize.width === 0) {
      setScreenSize(getCurrentDimension());
    }
    if (toastStatus === false) {
      showToast();
      setToastStatus(true);
    }
  }, [paymentStatus, token, toastStatus, screenSize]);

  return (
    <div>
      <Toaster
        position={screenSize.width <= 1030 ? "bottom-right" : "top-right"}
        richColors
      />
    </div>
  );
}

export default function Billing() {
  const { data, isLoading, isSuccess, isError } = useGetBalance();

  const getIP = useGetIP();
  const [userCountry, setUserCountry] = useState("");

  useEffect(() => {
    if (localStorage.getItem("country") != null && userCountry === "") {
      setUserCountry(localStorage.getItem("country") || "");
    } else {
      // getIP.refetch();
      setUserCountry("US");
      localStorage.setItem("country", "US");
    }
    // if (getIP.isSuccess) {
    //   setUserCountry(getIP.data.country);
    //   localStorage.setItem("country", getIP.data.country);
    // }
    // if (getIP.isError) {
    //   setUserCountry("US");
    // }
  }, [userCountry]);

  return (
    <div>
      <head>
        <title>Tnsr.ai - Billing</title>
      </head>
      <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] grid-rows-[minmax(62px,_90px)_1fr]">
        <div className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-span-2 hidden lg:block">
          <div className="fixed top-0 h-full">
            <SideDrawer></SideDrawer>
          </div>
        </div>
        <div className="sticky top-0 z-50">
          <AppBar />
        </div>
        <div className="mt-5">
          <div className="lg:col-start-2 lg:col-end-3 lg:row-start-2 mt-5 mb-10">
            <div className="max-w-[1500px] m-auto">
              {isLoading === true && (
                <div className="flex mt-10 md:mt-5 justify-center">
                  <Loader color="grape" variant="bars" />
                </div>
              )}

              {isSuccess === true &&
                data.detail === "Success" &&
                userCountry != "" && (
                  <div>
                    <BillingContent data={data} />
                    <PricingTab country={userCountry} />
                    <InvoiceTable />
                  </div>
                )}
              {isError === true && <Error />}
            </div>
          </div>
        </div>
        <div>
          <Suspense
            fallback={
              <div>
                <Loader color="grape" />
              </div>
            }
          >
            <ShowToast />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
