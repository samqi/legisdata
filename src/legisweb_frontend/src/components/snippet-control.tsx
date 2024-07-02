import { ForwardedRef, forwardRef, useRef } from "react";
import {
  Button,
  ButtonGroup,
  Form,
  InputGroup,
  OverlayTrigger,
  Popover,
} from "react-bootstrap";
import * as Icon from "react-bootstrap-icons";
import { useDispatch } from "react-redux";
import { toggle } from "../features/content-element/content-element-slice";
import { show as toastShow } from "../features/toast/toast-slice";
import * as Schema from "../schema";

function contentGenerateUrl(generatedId: string): string {
  const url = new URL(window.location.href);
  url.hash = "#".concat(generatedId);

  return url.toString();
}

const CopyPopup = forwardRef(
  (
    { handleClick, value }: { handleClick: () => void; value: string },
    ref: ForwardedRef<HTMLInputElement>
  ) => (
    <Popover.Body>
      <Form.Label>Share a link to this snippet</Form.Label>
      <InputGroup>
        <Form.Control readOnly={true} value={value} ref={ref}></Form.Control>
        <Button onClick={handleClick}>
          <Icon.Copy />
        </Button>
      </InputGroup>
    </Popover.Body>
  )
);

export default function SpeakSnippetControl({
  content,
  contentIdx,
  displayText,
}: {
  content: Schema.ContentElement;
  contentIdx: string;
  displayText: boolean;
}) {
  const ref = useRef(null);
  const dispatch = useDispatch();

  return (
    <ButtonGroup size="sm" className="float-end">
      <OverlayTrigger
        placement="auto"
        trigger="click"
        rootClose={true}
        overlay={
          <Popover>
            <CopyPopup
              ref={ref}
              value={contentGenerateUrl(contentIdx)}
              handleClick={() => {
                // @ts-expect-error API
                ref.current.select();

                // @ts-expect-error API
                navigator.clipboard.writeText(ref.current.value);

                dispatch(
                  toastShow({
                    variant: "success",
                    message: "Link is copied to clipboard.",
                  })
                );
              }}
            />
          </Popover>
        }
      >
        <Button variant="secondary">
          <Icon.Share />
        </Button>
      </OverlayTrigger>
      <Button
        variant="secondary"
        disabled={content.image == null}
        onClick={() => dispatch(toggle(contentIdx))}
      >
        {displayText ? <Icon.CardImage /> : <Icon.CardText />}
      </Button>
    </ButtonGroup>
  );
}
