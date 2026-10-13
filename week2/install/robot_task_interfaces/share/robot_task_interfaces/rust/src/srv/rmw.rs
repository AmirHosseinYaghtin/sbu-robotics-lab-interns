#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "robot_task_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__srv__GetRobotStatus_Request() -> *const std::ffi::c_void;
}

#[link(name = "robot_task_interfaces__rosidl_generator_c")]
extern "C" {
    fn robot_task_interfaces__srv__GetRobotStatus_Request__init(msg: *mut GetRobotStatus_Request) -> bool;
    fn robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetRobotStatus_Request>, size: usize) -> bool;
    fn robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetRobotStatus_Request>);
    fn robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetRobotStatus_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<GetRobotStatus_Request>) -> bool;
}

// Corresponds to robot_task_interfaces__srv__GetRobotStatus_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetRobotStatus_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for GetRobotStatus_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_task_interfaces__srv__GetRobotStatus_Request__init(&mut msg as *mut _) {
        panic!("Call to robot_task_interfaces__srv__GetRobotStatus_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetRobotStatus_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetRobotStatus_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetRobotStatus_Request where Self: Sized {
  const TYPE_NAME: &'static str = "robot_task_interfaces/srv/GetRobotStatus_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__srv__GetRobotStatus_Request() }
  }
}


#[link(name = "robot_task_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__srv__GetRobotStatus_Response() -> *const std::ffi::c_void;
}

#[link(name = "robot_task_interfaces__rosidl_generator_c")]
extern "C" {
    fn robot_task_interfaces__srv__GetRobotStatus_Response__init(msg: *mut GetRobotStatus_Response) -> bool;
    fn robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetRobotStatus_Response>, size: usize) -> bool;
    fn robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetRobotStatus_Response>);
    fn robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetRobotStatus_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<GetRobotStatus_Response>) -> bool;
}

// Corresponds to robot_task_interfaces__srv__GetRobotStatus_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetRobotStatus_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub status: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub current_action: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub elapsed_time: f64,

}



impl Default for GetRobotStatus_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_task_interfaces__srv__GetRobotStatus_Response__init(&mut msg as *mut _) {
        panic!("Call to robot_task_interfaces__srv__GetRobotStatus_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetRobotStatus_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetRobotStatus_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetRobotStatus_Response where Self: Sized {
  const TYPE_NAME: &'static str = "robot_task_interfaces/srv/GetRobotStatus_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__srv__GetRobotStatus_Response() }
  }
}






#[link(name = "robot_task_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__robot_task_interfaces__srv__GetRobotStatus() -> *const std::ffi::c_void;
}

// Corresponds to robot_task_interfaces__srv__GetRobotStatus
#[allow(missing_docs, non_camel_case_types)]
pub struct GetRobotStatus;

impl rosidl_runtime_rs::Service for GetRobotStatus {
    type Request = GetRobotStatus_Request;
    type Response = GetRobotStatus_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__robot_task_interfaces__srv__GetRobotStatus() }
    }
}


