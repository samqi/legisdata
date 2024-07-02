import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface ToastState {
  show: boolean;
  variant: string;
  message: string;
}

const initialState: ToastState = {
  show: false,
  message: "Hello world",
  variant: "info",
};

export const toastSlice = createSlice({
  name: "alert",
  initialState,
  reducers: {
    show(
      state: ToastState,
      action: PayloadAction<{ variant: string; message: string }>
    ) {
      state.show = true;
      state.message = action.payload.message;
      state.variant = action.payload.variant;
    },

    hide(state: ToastState) {
      state.show = false;
    },
  },
});

export const { show, hide } = toastSlice.actions;

export default toastSlice.reducer;
