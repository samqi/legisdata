import { configureStore, Store } from "@reduxjs/toolkit";
import contentElementReducer from "../features/content-element/content-element-slice";
import toastReducer from "../features/toast/toast-slice";

export const store: Store = configureStore({
  reducer: {
    contentElement: contentElementReducer,
    toast: toastReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
