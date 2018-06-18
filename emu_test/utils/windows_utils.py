# Copyright 2017 Cloudbase Solutions Srl
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ctypes
import logging
import os

LOG = logging.getLogger()


FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
FORMAT_MESSAGE_ALLOCATE_BUFFER = 0x00000100
FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200

JobObjectBasicLimitInformation = 2
JobObjectExtendedLimitInformation = 9

# If the following flag is set, all processes associated with
# the job are terminated when the last job handle is closed.
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000


HANDLE = ctypes.c_void_p


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('ReadOperationCount', ctypes.c_ulonglong),
        ('WriteOperationCount', ctypes.c_ulonglong),
        ('OtherOperationCount', ctypes.c_ulonglong),
        ('ReadTransferCount', ctypes.c_ulonglong),
        ('WriteTransferCount', ctypes.c_ulonglong),
        ('OtherTransferCount', ctypes.c_ulonglong)
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('PerProcessUserTimeLimit', ctypes.c_ulonglong),
        ('PerJobUserTimeLimit', ctypes.c_ulonglong),
        ('LimitFlags', ctypes.c_ulong),
        ('MinimumWorkingSetSize', ctypes.c_size_t),
        ('MaximumWorkingSetSize', ctypes.c_size_t),
        ('ActiveProcessLimit', ctypes.c_ulong),
        ('Affinity', ctypes.POINTER(ctypes.c_ulong)),
        ('PriorityClass', ctypes.c_ulong),
        ('SchedulingClass', ctypes.c_ulong)
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ('IoInfo', IO_COUNTERS),
        ('ProcessMemoryLimit', ctypes.c_size_t),
        ('JobMemoryLimit', ctypes.c_size_t),
        ('PeakProcessMemoryUsed', ctypes.c_size_t),
        ('PeakJobMemoryUsed', ctypes.c_size_t)
    ]


if os.name == "nt":
    global kernel32
    kernel32 = ctypes.windll.kernel32

    kernel32.CloseHandle.argtypes = [HANDLE]
    kernel32.CloseHandle.restype = ctypes.c_ulong

    kernel32.FormatMessageA.argtypes = [
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_void_p
    ]
    kernel32.FormatMessageA.restype = ctypes.c_ulong

    kernel32.LocalFree.argtypes = [HANDLE]
    kernel32.LocalFree.restype = HANDLE

    kernel32.GetLastError.argtypes = []
    kernel32.GetLastError.restype = ctypes.c_ulong

    kernel32.SetLastError.argtypes = [ctypes.c_ulong]
    kernel32.SetLastError.restype = None

    kernel32.CreateJobObjectW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p
    ]
    kernel32.CreateJobObjectW.restype = HANDLE

    kernel32.SetInformationJobObject.argtypes = [
        HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_ulong
    ]
    kernel32.SetInformationJobObject.restype = ctypes.c_long

    kernel32.AssignProcessToJobObject.argtypes = [
        HANDLE,
        HANDLE
    ]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_long

    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = HANDLE
else:
    kernel32 = None


class WinUtilsException(Exception):
    msg_fmt = 'An exception has been encountered.'

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs
        self.error_code = kwargs.get('error_code')

        if not message:
            message = self.msg_fmt % kwargs

        self.message = message
        super(WinUtilsException, self).__init__(message)


class Win32Exception(WinUtilsException):
    msg_fmt = ("Executing Win32 API function %(func_name)s failed. "
               "Error code: %(error_code)s. "
               "Error message: %(error_message)s")


class ProcessUtils(object):
    _kernel32_lib_func_opts = dict(error_on_nonzero_ret_val=False,
                                   ret_val_is_err_code=False)

    def _call_win32_func(self, *args, **kwargs):
        kwargs.update(kernel32_lib_func=True)
        return self.call_win32_func(*args, **kwargs)

    def call_win32_func(self, func, *args, **kwargs):
        """Convenience helper method for running Win32 API methods."""
        kernel32_lib_func = kwargs.pop('kernel32_lib_func', False)
        if kernel32_lib_func:
            kwargs['error_ret_vals'] = kwargs.get('error_ret_vals', [0])
            kwargs.update(self._kernel32_lib_func_opts)

        ignored_error_codes = kwargs.pop('ignored_error_codes', [])

        # A list of return values signaling that the operation failed.
        error_ret_vals = kwargs.pop('error_ret_vals', [])
        error_on_nonzero_ret_val = kwargs.pop('error_on_nonzero_ret_val', True)
        ret_val_is_err_code = kwargs.pop('ret_val_is_err_code', True)

        # The exception raised when the Win32 API function fails. The
        # exception must inherit Win32Exception.
        failure_exc = kwargs.pop('failure_exc', Win32Exception)
        # Expects a dict containing error codes as keys and the
        # according error message codes as values. If the error code is
        # not present in this dict, this method will search the System
        # message table.
        error_msg_src = kwargs.pop('error_msg_src', {})

        ret_val = func(*args, **kwargs)

        func_failed = (error_on_nonzero_ret_val and ret_val) or (
            ret_val in error_ret_vals)

        if func_failed:
            error_code = (ret_val
                          if ret_val_is_err_code else self.get_last_error())
            error_code = ctypes.c_ulong(error_code).value
            if error_code not in ignored_error_codes:
                error_message = error_msg_src.get(error_code,
                                                  self.get_error_message(
                                                      error_code))
                func_name = getattr(func, '__name__', '')
                raise failure_exc(error_code=error_code,
                                  error_message=error_message,
                                  func_name=func_name)
        return ret_val

    @staticmethod
    def get_error_message(error_code):
        message_buffer = ctypes.c_char_p()

        kernel32.FormatMessageA(
            FORMAT_MESSAGE_FROM_SYSTEM |
            FORMAT_MESSAGE_ALLOCATE_BUFFER |
            FORMAT_MESSAGE_IGNORE_INSERTS,
            None, error_code, 0, ctypes.byref(message_buffer), 0, None)

        error_message = message_buffer.value
        kernel32.LocalFree(message_buffer)
        return error_message

    def get_last_error(self):
        error_code = kernel32.GetLastError()
        kernel32.SetLastError(0)
        return error_code

    def close_handle(self, handle):
        kernel32.CloseHandle(handle)

    def create_job_object(self, name=None):
        """Create or open a job object.

        :param name: (Optional) the job name.
        :returns: a handle of the created job.
        """
        pname = None if name is None else ctypes.c_wchar_p(name)
        return self._call_win32_func(
            kernel32.CreateJobObjectW,
            None,  # job security attributes
            pname,
            error_ret_vals=[None])

    def set_information_job_object(self, job_handle, job_object_info_class,
                                   job_object_info):
        self._call_win32_func(
            kernel32.SetInformationJobObject,
            job_handle,
            job_object_info_class,
            ctypes.byref(job_object_info),
            ctypes.sizeof(job_object_info))

    def assign_process_to_job_object(self, job_handle, process_handle):
        self._call_win32_func(
            kernel32.AssignProcessToJobObject,
            job_handle, process_handle)

    def run_as_job(self):
        """Associates a new job to the current process.

        The process is immediately killed when the last job handle is closed.
        This mechanism can be useful when ensuring that child processes get
        killed along with a parent process.

        This method does not check if the specified process is already part of
        a job. Starting with WS 2012, nested jobs are available.

        :returns: the job handle, if a job was successfully created and
                  associated with the process, otherwise "None".
        """

        process_handle = None
        job_handle = None
        job_associated = False

        try:
            process_handle = kernel32.GetCurrentProcess()
            job_handle = self.create_job_object()

            job_info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            job_info.BasicLimitInformation.LimitFlags = (
                JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
            job_info_class = JobObjectExtendedLimitInformation

            self.set_information_job_object(job_handle,
                                            job_info_class,
                                            job_info)

            self.assign_process_to_job_object(job_handle, process_handle)
            job_associated = True
        finally:
            if process_handle:
                self.close_handle(process_handle)

            if not job_associated and job_handle:
                # We have an unassociated job object. Closing the handle
                # will also destroy the job object.
                self.close_handle(job_handle)

        return job_handle
