"use client";
import * as React from "react";
import Modal from "@mui/material/Modal";
import { getCookie } from "cookies-next";
import { XMarkIcon } from "@heroicons/react/20/solid";
import Image from "next/image";
import { Slider } from "@mantine/core";
import { StarIcon } from "@heroicons/react/20/solid";
import { useState, useEffect } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { toast } from "sonner";

function increaseAndRound(numberVal: number, credits: number) {
  if (numberVal === 0) {
    return { original: 0, discounted: 0, percentage: 0 };
  }
  const roundedNo = Math.round(numberVal);
  if (roundedNo === 0) {
    return { original: 1, discounted: 0, percentage: 0 };
  }
  let discount = 0;
  if (credits >= 50 && credits < 100) {
    discount = 0.05; // 5% discount
  } else if (credits >= 100 && credits < 200) {
    discount = 0.1; // 10% discount
  } else if (credits >= 200 && credits < 300) {
    discount = 0.15; // 15% discount
  } else if (credits >= 300 && credits < 400) {
    discount = 0.2; // 20% discount
  } else if (credits >= 400 && credits <= 500) {
    discount = 0.25; // 25% discount
  }
  if (discount === 0) {
    return { original: roundedNo, discounted: 0, percentage: 0 };
  }
  return {
    original: roundedNo,
    discounted: Math.round(roundedNo * (1 - discount)),
    percentage: discount * 100,
  };
}

function getCurrentDimension() {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}

export default function BuyPrompt(props: any) {
  const [value, setValue] = useState(5);
  const [rates, setRates] = useState<any>([]);
  const [original, setOriginal] = useState(0);
  const [discounted, setDiscounted] = useState(0);
  const [percentage, setPercentage] = useState(0);
  const [screenSize, setScreenSize] = React.useState(getCurrentDimension());

  useEffect(() => {
    if (Object.keys(rates).length === 0) {
      try {
        const ratesFromStorage = sessionStorage.getItem("rates");
        const parsedRates = ratesFromStorage
          ? JSON.parse(ratesFromStorage)
          : {};
        setRates(parsedRates);
      } catch (error) {
        console.error("Failed to parse rates from sessionStorage:", error);
        setRates({});
      }
    } else {
      const country = localStorage.getItem("country");
      if (rates.country !== country) {
        sessionStorage.removeItem("rates");
        setRates({});
      } else {
        const roundedVal = increaseAndRound(value * rates.rate, value);
        setOriginal(roundedVal.original);
        setDiscounted(roundedVal.discounted);
        setPercentage(roundedVal.percentage);
      }
    }
  }, [value, rates, setDiscounted, setOriginal, setPercentage]);

  async function makePayment() {
    const jwt: string = getCookie("access_token") as string;
    const response = fetch(`${process.env.BASEURL}/billing/checkout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${jwt}`,
      },
      body: JSON.stringify({
        token: value,
        currency_code: rates.currency,
      }),
    });
    const data = await response.then((res) => res.json());
    const stripePromise = loadStripe(process.env.STRIPE_PUBLIC as string);
    const stripe = await stripePromise;
    try {
      const result = await stripe?.redirectToCheckout({
        sessionId: data.data.session_id,
      });
      if (result?.error) {
        toast.error(result.error.message);
      }
    } catch (error: any) {
      toast.error("Something went wrong. Please try again later.");
    }
  }

  return (
    <div data-testid="buy-prompt">
      <Modal
        open={props.renamePrompt}
        onClose={() => {
          props.setRenamePrompt(false);
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
        style={{ backdropFilter: "blur(1px)" }}
      >
        <div className="h-full w-full flex justify-center items-center">
          <div className="bg-white rounded-lg p-5 w-[80%] max-w-[800px] shadow-2xl">
            <div className="pl-2 w-[100%] flex justify-between">
              <Image
                src="/assets/mainlogo_trimmed.png"
                width={30}
                height={10}
                alt="logo"
                style={{ width: "auto", height: "auto" }}
              />
              <XMarkIcon
                className="w-[26px] cursor-pointer"
                onClick={() => {
                  props.setRenamePrompt(false);
                }}
              />
            </div>
            <div className="p-2 mt-5">
              <p className="text-black font-semibold text-2xl">
                Want to process more?
              </p>
              <p className="">
                Top up your account with credits and process videos, audios, and
                images like never before!
              </p>
            </div>
            <div className="p-2 mt-14">
              <div className="flex justify-between">
                <div className="flex justify-start items-center space-x-2 mb-2">
                  <StarIcon className="w-[30px] fill-yellow-500" />
                  {value <= 500 && (
                    <p className="text-base md:text-xl font-medium">{`${value} Credits`}</p>
                  )}
                  {percentage > 0 && (
                    <p className="text-base md:text-xl font-normal text-green-500">{`(${percentage}% Discount )`}</p>
                  )}
                  {value > 500 && (
                    <p className="text-base md:text-xl font-medium">{`Contact Us`}</p>
                  )}
                </div>
                <div className="flex justify-start items-center space-x-2 mb-2">
                  {value <= 500 && discounted <= 0 && (
                    <p className="text-base md:text-xl font-medium">{`${rates.symbol} ${original}`}</p>
                  )}
                  {value <= 500 && discounted > 0 && (
                    <p className="text-base md:text-xl font-medium text-red-500 line-through">{`${rates.symbol} ${original}`}</p>
                  )}
                  {discounted > 0 && (
                    <p className="text-base md:text-xl font-medium">{`${rates.symbol} ${discounted}`}</p>
                  )}
                </div>
              </div>
              <Slider
                value={value}
                onChange={setValue}
                color="grape"
                size={"lg"}
                min={5}
                max={501}
                label={null}
              />
              <div className="mt-8">
                <p className="text-base font-normal">
                  Need more credits? Contact{" "}
                  <a
                    className="text-base font-medium"
                    href="mailto:admin@tnsr.ai"
                  >
                    admin@tnsr.ai
                  </a>
                </p>
              </div>
              <div className="mt-5 w-full flex justify-end">
                <button
                  type="button"
                  className="rounded-md bg-purple-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
                  onClick={makePayment}
                >
                  Continue to Checkout
                </button>
              </div>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
