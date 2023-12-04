"use client";
import { useState, useEffect } from "react";
import { useGetInvoice } from "../api/index";
import { Loader } from "@mantine/core";
import Image from "next/image";
import { Pagination } from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import { MinusSmallIcon } from "@heroicons/react/20/solid";
import { getCookie } from "cookies-next";
import { toast } from "sonner";

export default function InvoiceTable() {
  const queryClient = useQueryClient();
  const limit = 5;
  const [offset, setOffset] = useState(0);
  const { data, isLoading, isSuccess, refetch, isError } =
    useGetInvoice(limit, offset);
  const [invoiceId, setInvoiceId] = useState("");
  const [download, setDownload] = useState(false);

  const downloadInvoice = async () => {
    toast("Downloading invoice...");
    const url = `${process.env.BASEURL}/billing/download_invoice/?invoice_id=${invoiceId}`;
    const jwt = getCookie("access_token");
    const response = fetch(url, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${jwt}`,
      },
    });
    if ((await response).status != 200) {
      toast.error("Unauthorized");
      return;
    }
    response.then((res) => {
      res.blob().then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `#${invoiceId + 1000}.pdf`;
        a.click();
      });
    });
    toast.success("Invoice downloaded successfully");
  };

  useEffect(() => {
    if (download === true) {
      downloadInvoice();
      setDownload(false);
    }
  }, [offset, data, refetch, invoiceId, download]);
  return (
    <div>
      {isLoading === true && (
        <div className="flex mt-10 md:mt-5 justify-center">
          <Loader color="grape" variant="bars" />
        </div>
      )}
      {isSuccess === true && (
        <div className="px-10 mb-10 mt-5">
          <div className="sm:flex sm:items-center">
            <div className="sm:flex-auto">
              <h1 className="text-2xl font-semibold mt-3 ml-5">Invoices</h1>
            </div>
          </div>
          <div className="-mx-4 mt-8 overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:-mx-6 md:mx-0 md:rounded-lg">
            <table className="min-w-full divide-y divide-gray-300 rounded-2xl">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    scope="col"
                    className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6"
                  >
                    Order
                  </th>
                  <th
                    scope="col"
                    className="hidden px-3 py-3.5 text-left text-sm font-semibold text-gray-900 sm:table-cell"
                  >
                    Date
                  </th>
                  <th
                    scope="col"
                    className="hidden px-3 py-3.5 text-left text-sm font-semibold text-gray-900 lg:table-cell"
                  >
                    Source
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                  >
                    Amount
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                  >
                    Status
                  </th>
                  <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span className="sr-only">Edit</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {data.data.map((invoice: any) => (
                  <tr key={invoice.orderID}>
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                      {`#${invoice.orderID + 1000}`}
                    </td>
                    <td className="hidden whitespace-nowrap px-3 py-4 text-sm text-gray-500 sm:table-cell">
                      {invoice.date}
                    </td>
                    <td className="hidden whitespace-nowrap px-3 py-4 text-sm  lg:table-cell">
                      <div className="flex space-x-1 justify-start">
                        {invoice.payment_details.card != null && (
                          <Image
                            src={`/card_logo/${invoice.payment_details.card}.svg`}
                            alt="Visa"
                            width={30}
                            height={30}
                          />
                        )}
                        {invoice.payment_details.last4 != null && (
                          <p className="text-gray-500">
                            {`** ${invoice.payment_details.last4}`}
                          </p>
                        )}
                        {invoice.payment_details.last4 == null && (
                          <div className="w-full flex justify-start">
                            <MinusSmallIcon className="w-[20px] fill-gray-500" />
                          </div>
                        )}
                      </div>
                    </td>

                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {`${invoice.currency} ${invoice.amount}`}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4">
                      {invoice.status.toLowerCase() === "completed" && (
                        <span className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
                          {invoice.status}
                        </span>
                      )}
                      {invoice.status.toLowerCase() === "pending" && (
                        <span className="inline-flex items-center rounded-md bg-yellow-50 px-2 py-1 text-xs font-medium text-yellow-700 ring-1 ring-inset ring-yellow-600/20">
                          {invoice.status}
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      {invoice.status.toLowerCase() === "completed" && (
                        <p
                          className="text-purple-600 hover:text-purple-900 cursor-pointer"
                          onClick={() => {
                            setInvoiceId(invoice.orderID);
                            setDownload(true);
                          }}
                        >
                          Download
                        </p>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="w-full flex justify-center mt-5" id="pageInvoice">
            <Pagination
              total={Math.ceil(data.total / limit)}
              color="grape"
              withEdges
              value={Math.ceil(offset / limit) + 1}
              onChange={(page) => {
                queryClient.invalidateQueries({
                  queryKey: ["/billing/get_invoices"],
                });
                setOffset((page - 1) * limit);
                refetch();

                const element = document.getElementById("pageInvoice");
                const y = element?.getBoundingClientRect().top as number;
                const top = window.pageYOffset + y;
                window.scrollTo({ top: top, behavior: "smooth" });
              }}
            />
          </div>
        </div>
      )}
      {isError === true && (
        <div className="flex mt-10 md:mt-5 justify-center">
          <p className="text-2xl font-semibold">Unable to fetch invoice data</p>
        </div>
      )}
    </div>
  );
}
