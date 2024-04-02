import { useState, useEffect } from "react";
import Modal from "@mui/material/Modal";
import { getCookie } from "cookies-next";
import { XMarkIcon } from "@heroicons/react/20/solid";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const isAlphaNumeric = (str: string) => {
  var alphanumericPattern = /^[a-zA-Z0-9_ ]+$/;
  return alphanumericPattern.test(str);
};

export default function RenamePrompt(props: any) {
  const jwt: string = getCookie("access_token") as string;
  let title;
  title = props.title;
  const lastDotIndex = title.lastIndexOf(".");
  let ext = "";
  if (lastDotIndex === -1) {
    title = title;
  } else {
    ext = title.slice(lastDotIndex, title.length);
    title = title.slice(0, lastDotIndex);
  }

  const [newtitle, setNewtitle] = useState("");
  const [btnDisabled, setBtnDisabled] = useState(true);
  const [titleError, setTitleError] = useState("hidden");
  const [errorText, setErrorText] = useState("");
  let header;
  let api_endpoint: string;
  let query_key: string;
  if (props.project === true) {
    header = "Rename Project";
    api_endpoint = "/options/rename-project";
    query_key = "/content/get_content";
  } else {
    header = "Rename File";
    api_endpoint = "/content/rename-content";
    query_key = "/content/get_content_list";
  }

  const { mutate } = useMutation(
    ({
      id,
      type,
      newtitle_,
    }: {
      id: number;
      type: string;
      newtitle_: string;
    }) => {
      let newtitleName = newtitle_ + ext;
      const url = `${process.env.BASEURL}${api_endpoint}/${id}/${type}/${newtitleName}`;
      return fetch(url, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${jwt}`,
        },
      });
    }
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewtitle(e.target.value);
  };

  const queryClient = useQueryClient();

  useEffect(() => {
    if (newtitle.length >= 30) {
      setTitleError("block");
      setErrorText("Filename must be less than 30 characters.");
      setBtnDisabled(true);
    }
    if (isAlphaNumeric(newtitle) === false) {
      setTitleError("block");
      setErrorText("Filename must be alphanumeric.");
      setBtnDisabled(true);
    }
    if (newtitle.length < 3) {
      setTitleError("block");
      setErrorText("Filename must be at least 3 characters.");
      setBtnDisabled(true);
    }
    if (
      newtitle.length >= 3 &&
      newtitle.length < 30 &&
      isAlphaNumeric(newtitle) === true
    ) {
      setTitleError("hidden");
      setErrorText("");
      setBtnDisabled(false);
    }
    if (newtitle.length === 0) {
      setTitleError("hidden");
      setErrorText("");
      setBtnDisabled(true);
    }
  }, [newtitle, btnDisabled]);

  return (
    <div>
      <Modal
        open={props.renamePrompt}
        onClose={() => {
          props.setRenamePrompt(false);
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <div className="h-full w-full flex justify-center items-center">
          <div className="bg-white rounded-lg p-5">
            <div className="pl-2 md:w-[456px] flex justify-between">
              <h1 className="font-semibold text-lg lg:text-lg xl:text-xl">
                {header}
              </h1>
              <XMarkIcon
                className="w-[26px] cursor-pointer"
                onClick={() => {
                  props.setRenamePrompt(false);
                }}
              />
            </div>
            <div className="p-2">
              <p className="text-sm md:text-base">
                Enter a new name for the project.{" "}
                <span className="text-sm md:text-base font-medium">
                  Only filename is required.
                </span>
              </p>
              <div className="w-full">
                <input
                  type="text"
                  name="renameText"
                  required
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100"
                  onChange={handleChange}
                  placeholder={title}
                />
                <div className={titleError}>
                  <label className="font-medium tracking-tighter text-red-600">
                    {errorText}
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end items-center p-2 space-x-5 mt-3">
              <button
                type="button"
                className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                onClick={() => {
                  props.setRenamePrompt(false);
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="rounded-md bg-purple-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600 disabled:text-gray-50 disabled:bg-purple-200"
                onClick={() => {
                  mutate({
                    id: props.id,
                    type: props.type,
                    newtitle_: newtitle,
                  });
                  props.setRenamePrompt(false);
                  queryClient.invalidateQueries({
                    queryKey: [query_key],
                  });
                  window.location.reload();
                }}
                disabled={btnDisabled}
              >
                Rename
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
