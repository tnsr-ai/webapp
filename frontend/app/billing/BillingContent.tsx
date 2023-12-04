"use client";
import { ShoppingCartIcon } from "@heroicons/react/20/solid";
import { useState } from "react";
import BuyPrompt from "../components/ModalComponents/BuyModal";

export default function BillingContent(props: any) {
  const [buyPrompt, setBuyPrompt] = useState(false);
  return (
    <div>
      <div>
        <h1 className="text-2xl font-semibold ml-5 mb-5">Billing</h1>
      </div>
      <div id="billing-tab">
        <div className="flex-row xl:flex mt-5 px-6 gap-5 ">
          <div className="bg-purple-200 rounded-xl md:flex-[6] h-[300px] md:h-[244px] shadow-[0_3px_10px_rgb(0,0,0,0.2)]">
            <div className="flex flex-col items-start justify-start h-full">
              <h1
                className="text-center font-semibold text-2xl pt-5 pl-5"
                data-testid="tokenHeader"
              >
                Token Balance
              </h1>
              <div className="flex flex-row gap-10">
                <h1 className="text-left font-normal text-base md:text-lg pt-5 pl-5">
                  Current Balance: <br className="block md:hidden" />{" "}
                  {props.data.data.balance} credits
                </h1>
                <h1 className="text-left font-normal text-base md:text-lg pt-5 pl-5">
                  Lifetime Usage: <br className="block md:hidden" />{" "}
                  {props.data.data.lifetime_usage} credits
                </h1>
              </div>
              <h1 className="text-left font-normal text-base md:text-lg pt-2 pl-5">
                Plan: {props.data.data.tier}
              </h1>
              <h1 className="text-left font-medium text-base md:text-lg pt-2 pl-5">
                No Expiry
              </h1>
              <div className="pt-3 pl-5">
                <button
                  type="button"
                  className="inline-flex items-center rounded-md border border-transparent bg-purple-600 px-3 py-2 text-sm font-normal leading-4 text-white shadow-sm hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                  onClick={() => {
                    setBuyPrompt(true);
                  }}
                >
                  <ShoppingCartIcon
                    className="-ml-0.5 mr-2 h-4 w-4"
                    aria-hidden="true"
                    onClick={() => {
                      setBuyPrompt(true);
                    }}
                  />
                  Buy Tokens
                </button>
                <BuyPrompt
                  renamePrompt={buyPrompt}
                  setRenamePrompt={setBuyPrompt}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
