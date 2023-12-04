"use client";
import { useGetRates } from "../api/index";
import { useEffect, useState } from "react";
import { userPlans } from "../constants/constants";
import { increaseAndRound } from "../utils/utils";

interface PricingTabProps {
  country: string;
}

export default function PricingTab(props: PricingTabProps) {
  const { data, isSuccess, refetch } = useGetRates(props.country);

  const [rates, setRates] = useState<any>(() => {
    try {
      const ratesFromStorage = sessionStorage.getItem("rates");
      return ratesFromStorage ? JSON.parse(ratesFromStorage) : {};
    } catch (error) {
      return {};
    }
  });

  useEffect(() => {
    if (Object.keys(rates).length === 0) {
      const ratesFromStorage = sessionStorage.getItem("rates");
      try {
        const parsedRates = ratesFromStorage
          ? JSON.parse(ratesFromStorage)
          : {};
        setRates(parsedRates);
      } catch (error) {
        refetch();
      }
    }
  }, [rates, refetch]);

  useEffect(() => {
    if (isSuccess && data && data.data) {
      setRates(data.data);
      sessionStorage.setItem("rates", JSON.stringify(data.data));
    }
  }, [isSuccess, data]);

  return (
    <section className="mt-10">
      <div className="w-[100%] text-gray-600 px-8">
        <div className="flex flex-col w-[100%] items-center mt-5">
          <h3 className="text-gray-800 text-3xl font-semibold sm:text-4xl">
            Pricing Tier
          </h3>
          <div className="mt-3 max-w-xl">
            <p>
              No subscription required. Tier is based on how much you use the
              service.
            </p>
          </div>
        </div>
        <div className="flex justify-center m-auto">
          <div className="w-[100%] mt-5 space-y-6 justify-center gap-6 grid grid-cols-1 md:grid-cols-2 sm:space-y-0 xl:grid-cols-3 ">
            {userPlans.map((item, idx) => (
              <div
                key={idx}
                className="flex-1 flex items-stretch flex-col p-8 rounded-xl border-2"
              >
                <div>
                  <span className="text-indigo-600 font-medium">
                    {item.name}
                  </span>
                  <div className="mt-4 text-gray-800 text-3xl font-semibold">
                    {`${rates.symbol} ${increaseAndRound(
                      rates.rate * item.times
                    )}`}{" "}
                    <span className="text-xl text-gray-600 font-normal">
                      spent
                    </span>
                  </div>
                </div>
                <ul className="py-8 space-y-3">
                  {item.features.map((featureItem, idx) => (
                    <li key={idx} className="flex items-center gap-5">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5 text-indigo-600"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        ></path>
                      </svg>
                      {featureItem}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
