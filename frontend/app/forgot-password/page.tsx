"use client";
import GradientBar from "../components/GradientComponent/GradientBar";
import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { setForgotPassword } from "../api/index";
import { Loader } from "@mantine/core";
import { isValidEmail } from "../utils/utils";

export default function Forgot() {
  const [message, setMessage] = useState("");
  const [labelColor, setLabelColor] = useState("text-red-600");
  const [run, setRun] = useState(false);
  const { mutate, isLoading, isSuccess, data } = useMutation((formData) =>
    setForgotPassword(formData as any)
  );

  const [email, setEmail] = useState("");
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEmail(value);
  };
  const [emailAlert, setEmailAlert] = useState("hidden ");
  const [disabled, setDisabled] = useState(true);

  const resetPassword = () => {
    const formData = {
      email: email,
    };
    mutate(formData as any);
    setRun(true);
  };

  useEffect(() => {
    if (email.length >= 2 && !isValidEmail(email)) {
      setMessage("Invalid Email");
      setLabelColor("text-red-600");
      setEmailAlert("block");
    }
    if (email.length >= 2 && isValidEmail(email)) {
      setMessage("");
      setEmailAlert("hidden");
    }
    if (email.length == 0) {
      setMessage("");
      setEmailAlert("hidden");
    }
    if (email && isValidEmail(email)) {
      setMessage("");
      setDisabled(false);
    } else {
      setMessage("Invalid Email");
      setDisabled(true);
    }
    if (isSuccess === true) {
      if (data.detail === "Success") {
        setMessage(data.data);
        setLabelColor("text-green-600");
        setEmailAlert("block");
        if (run === true) {
          setEmail("");
          setRun(false);
        }
      } else {
        setMessage(data.data);
        setLabelColor("text-red-600");
        setEmailAlert("block");
      }
    }
  }, [email, message, labelColor, emailAlert, disabled, isSuccess]);

  return (
    <div className="grid lg:grid-cols-[30%_70%] w-full">
      <head>
        <title>Tnsr.ai - Forgot Password</title>
      </head>
      <GradientBar />
      <div className="w-full h-full flex justify-center items-center">
        <div
          className="flex-col justify-center items-center text-black"
          data-testid="forgotForm"
        >
          <h1 className="text-center font-semibold text-2xl lg:text-3xl mt-[2em] lg:mt-0 tracking-tight">
            Forgot Password ?
          </h1>
          <h1 className="text-center font-normal text-lg lg:text-xl mt-2 lg:mt-3 text-gray-400 tracking-tight">
            Enter your email to reset your password
          </h1>
          <form>
            <div className="mt-3 md:mt-5">
              <label className="font-medium tracking-tight">Email</label>
              <input
                type="email"
                name="email"
                required
                onChange={handleChange}
                value={email}
                data-testid="emailInput"
                className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-100"
              />
              <div className={`${emailAlert} pt-3`}>
                <label className={`font-medium tracking-tighter ${labelColor}`}>
                  {message}
                </label>
              </div>
            </div>
          </form>
          <div className="flex justify-center space-x-5 lg:space-x-8 mt-3 md:mt-5">
            {isLoading === false && (
              <button
                className="w-full px-4 py-2 text-white font-medium bg-purple-600 hover:bg-purple-500 active:bg-purple-600 rounded-lg duration-300 tracking-tight disabled:opacity-50 disabled:hover:opacity-50 disabled:cursor-not-allowed"
                disabled={disabled}
                onClick={resetPassword}
                data-testid="resetPasswordButton"
              >
                Submit
              </button>
            )}
            {isLoading === true && (
              <div className="flex justify-center items-center">
                <Loader color="grape" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
