#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "robot_task_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__msg__Waypoint() -> *const std::ffi::c_void;
}

#[link(name = "robot_task_interfaces__rosidl_generator_c")]
extern "C" {
    fn robot_task_interfaces__msg__Waypoint__init(msg: *mut Waypoint) -> bool;
    fn robot_task_interfaces__msg__Waypoint__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Waypoint>, size: usize) -> bool;
    fn robot_task_interfaces__msg__Waypoint__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Waypoint>);
    fn robot_task_interfaces__msg__Waypoint__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Waypoint>, out_seq: *mut rosidl_runtime_rs::Sequence<Waypoint>) -> bool;
}

// Corresponds to robot_task_interfaces__msg__Waypoint
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Waypoint {

    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub theta: f64,

}



impl Default for Waypoint {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_task_interfaces__msg__Waypoint__init(&mut msg as *mut _) {
        panic!("Call to robot_task_interfaces__msg__Waypoint__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Waypoint {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__msg__Waypoint__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__msg__Waypoint__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__msg__Waypoint__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Waypoint {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Waypoint where Self: Sized {
  const TYPE_NAME: &'static str = "robot_task_interfaces/msg/Waypoint";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__msg__Waypoint() }
  }
}


#[link(name = "robot_task_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__msg__MoveCommand() -> *const std::ffi::c_void;
}

#[link(name = "robot_task_interfaces__rosidl_generator_c")]
extern "C" {
    fn robot_task_interfaces__msg__MoveCommand__init(msg: *mut MoveCommand) -> bool;
    fn robot_task_interfaces__msg__MoveCommand__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<MoveCommand>, size: usize) -> bool;
    fn robot_task_interfaces__msg__MoveCommand__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<MoveCommand>);
    fn robot_task_interfaces__msg__MoveCommand__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<MoveCommand>, out_seq: *mut rosidl_runtime_rs::Sequence<MoveCommand>) -> bool;
}

// Corresponds to robot_task_interfaces__msg__MoveCommand
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MoveCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub action_label: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub waypoints: rosidl_runtime_rs::Sequence<super::super::msg::rmw::Waypoint>,

}



impl Default for MoveCommand {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_task_interfaces__msg__MoveCommand__init(&mut msg as *mut _) {
        panic!("Call to robot_task_interfaces__msg__MoveCommand__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for MoveCommand {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__msg__MoveCommand__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__msg__MoveCommand__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_task_interfaces__msg__MoveCommand__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for MoveCommand {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for MoveCommand where Self: Sized {
  const TYPE_NAME: &'static str = "robot_task_interfaces/msg/MoveCommand";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_task_interfaces__msg__MoveCommand() }
  }
}


