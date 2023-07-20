/**
 * State management for cards retrieved from the backend.
 */

import { createSlice } from "@reduxjs/toolkit";

import { APIGetCards } from "@/app/api";
import { AppDispatch } from "@/app/store";
import { CardEndpointPageSize } from "@/common/constants";
import { CardDocumentsState, createAppAsyncThunk } from "@/common/types";
import { CardDocuments } from "@/common/types";
import { fetchCardbacksAndReportError } from "@/features/card/cardbackSlice";
import { selectUniqueCardIdentifiers } from "@/features/project/projectSlice";
import { fetchSearchResultsAndReportError } from "@/features/search/searchResultsSlice";
import { setError } from "@/features/toasts/toastsSlice";

const typePrefix = "cardDocuments/fetchCardDocuments";

const fetchCardDocuments = createAppAsyncThunk(
  typePrefix,
  async (arg, { dispatch, getState }) => {
    /**
     * This function queries card documents (entire database rows) from the backend. It only queries cards which have
     * not yet been queried.
     */

    await fetchSearchResultsAndReportError(dispatch);
    await fetchCardbacksAndReportError(dispatch);

    const state = getState();

    const allIdentifiers = selectUniqueCardIdentifiers(state);
    const identifiersWithKnownData = new Set(
      Object.keys(state.cardDocuments.cardDocuments)
    );
    const identifiersToSearch = Array.from(
      new Set(
        Array.from(allIdentifiers).filter(
          (item) => !identifiersWithKnownData.has(item)
        )
      )
    );

    const pages = Array.from(
      Array(Math.ceil(identifiersToSearch.length / CardEndpointPageSize)).keys()
    );
    const backendURL = state.backend.url;
    if (identifiersToSearch.length > 0 && backendURL != null) {
      // this block of code looks a bit arcane.
      // we're dynamically constructing a promise chain according to the number of requests we need to make
      // to retrieve all database rows corresponding to `identifiersToSearch`.
      // e.g. say that `identifiersToSearch` contains 1500 identifiers.
      // two requests will be issued, the first for 1000 cards, and the second for 500 cards
      // (with the second request only commencing once the first has finished).
      return pages.reduce(function (
        promiseChain: Promise<CardDocuments>,
        page: number
      ) {
        return promiseChain.then(async function (previousValue: CardDocuments) {
          const cards = await APIGetCards(
            backendURL,
            identifiersToSearch.slice(
              page * CardEndpointPageSize,
              (page + 1) * CardEndpointPageSize
            )
          );
          return { ...previousValue, ...cards };
        });
      },
      Promise.resolve({}));
    }
  }
);

const initialState: CardDocumentsState = {
  cardDocuments: {},
  status: "idle",
  error: null,
};

export const cardDocumentsSlice = createSlice({
  name: "cardDocuments",
  initialState,
  reducers: {
    addCardDocuments: (state, action) => {
      state.cardDocuments = { ...state.cardDocuments, ...action.payload };
    },
  },
  extraReducers(builder) {
    builder
      .addCase(fetchCardDocuments.pending, (state, action) => {
        state.status = "loading";
      })
      .addCase(fetchCardDocuments.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.cardDocuments = { ...state.cardDocuments, ...action.payload };
      })
      .addCase(fetchCardDocuments.rejected, (state, action) => {
        state.status = "failed";
        state.error = {
          name: action.error.name ?? null,
          message: action.error.message ?? null,
        };
      });
  },
});

export default cardDocumentsSlice.reducer;

export async function fetchCardDocumentsAndReportError(dispatch: AppDispatch) {
  try {
    await dispatch(fetchCardDocuments()).unwrap();
  } catch (error: any) {
    dispatch(
      setError([typePrefix, { name: error.name, message: error.message }])
    );
    return null;
  }
}
