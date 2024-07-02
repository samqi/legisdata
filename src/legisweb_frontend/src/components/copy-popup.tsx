import { ForwardedRef, forwardRef } from "react";
import { Button, Form, InputGroup, Popover } from "react-bootstrap";
import * as Icon from "react-bootstrap-icons";

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

export default CopyPopup;
