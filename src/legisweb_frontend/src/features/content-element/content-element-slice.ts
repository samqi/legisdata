import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface ContentElementState {
  [id: string]: {
    displayText: boolean;
  };
}

const initialState: ContentElementState = {};

export const contentElementSlice = createSlice({
  name: "contentElement",
  initialState,
  reducers: {
    toggle(state: ContentElementState, action: PayloadAction<string>) {
      state[action.payload] = {
        displayText: !(state[action.payload]?.displayText ?? true),
      };
    },
  },
});

export const { toggle } = contentElementSlice.actions;

export default contentElementSlice.reducer;
